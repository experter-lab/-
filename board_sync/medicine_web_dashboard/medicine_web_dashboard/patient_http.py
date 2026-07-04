"""病人侧 web HTTP handler.

挂在 web_dashboard_node 的第二个 ThreadingHTTPServer (patient_port) 上,
serve 编译好的 dist/ + /patient/api/* 接口。

业务语境: 院内药品派送 (不是病人下单), 流程是
医嘱 → 药房备药 → 机器人配送 → 病人核对取药。

API (新):
  GET  /patient/api/delivery?bed=X
  GET  /patient/api/history?bed=X&days=Y
  GET  /patient/api/messages?bed=X
  POST /patient/api/deliveries/{id}/confirm   body: {bed}
  POST /patient/api/deliveries/{id}/reject    body: {reason, bed}
  POST /patient/api/call_robot                body: {bed, reason?}
  POST /patient/api/messages                  body: {bed, content, delivery_id?}

兼容旧路径:
  GET  /patient/api/order
  POST /patient/api/orders/{id}/{confirm,reject}

数据来源:
  - 当前派送: dashboard.latest_state (DeliveryState) + PATIENT_MEDICATION_ORDERS (mock 兜底)
  - 历史: dashboard.delivery_db.get_recent_batches() 过滤 bed_no
  - confirm/reject: 内存 override + 尝试调 verify_delivery_task service
  - call_robot: publish String JSON 到 /medicine/patient_call topic
"""

import gzip
import json
import base64
import hashlib
import hmac
import mimetypes
import os
import re
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote, urlparse

try:
    from .dashboard_assets import PATIENT_MEDICATION_ORDERS
except ImportError:  # pragma: no cover
    from dashboard_assets import PATIENT_MEDICATION_ORDERS


_BASE_PATH = "/patient/"
_API_PREFIX = "/patient/api/"

# DeliveryState.status -> patient 视角 DeliveryStatus 映射
# 默认值 = prescribed (院内开方语境的初态)
_STATUS_MAP = {
    # 兜底
    "": "prescribed",
    # task_manager 真实状态 (lowercase 后)
    "idle": "prescribed",
    "waiting_load_confirmation": "preparing",
    "navigating": "delivering",
    "waiting_dispense_confirmation": "arrived",
    "completed": "confirmed",
    "navigation_failed": "cancelled",
    # 旧别名 / 历史兼容
    "created": "prescribed",
    "pending": "prescribed",
    "queued": "prescribed",
    "prescribed": "prescribed",
    "loading": "preparing",
    "loaded": "preparing",
    "preparing": "preparing",
    "dispatched": "dispatched",
    "in_progress": "delivering",
    "delivering": "delivering",
    "transit": "delivering",
    "arrived": "arrived",
    "confirmed": "confirmed",
    "rejected": "rejected",
    "cancelled": "cancelled",
    "canceled": "cancelled",
}

# 前端 DeliveryStatus 联合类型的全集 (与 patient_web/src/lib/types.ts 对齐)
# = _STATUS_MAP.values() ∪ override 流允许的扩展枚举 (目前: timeout)
# 后端写 override 引入新 status 必须先把它加进这里 + 同步前端 STATUS_META, 否则前端整页崩
_VALID_PATIENT_STATUSES = set(_STATUS_MAP.values()) | {"timeout", "review"}


# ============================================================
# 可选床位访问 token
# ============================================================

def _b64url(data):
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _patient_token_signature(secret, bed, expires):
    msg = f"{str(bed).strip()}:{int(expires)}".encode("utf-8")
    digest = hmac.new(str(secret).encode("utf-8"), msg, hashlib.sha256).digest()
    return _b64url(digest)


def make_patient_access_token(secret, bed, ttl_sec=86400, now=None):
    """生成床位访问 token.

    格式: v1.<expires_unix>.<hmac>
    只绑定 bed 和过期时间, 不包含病人姓名/医嘱等敏感信息。
    """
    if not secret:
        return ""
    now = time.time() if now is None else float(now)
    expires = int(now + max(60, int(ttl_sec)))
    sig = _patient_token_signature(secret, bed, expires)
    return f"v1.{expires}.{sig}"


def verify_patient_access_token(secret, bed, token, now=None):
    """验证床位访问 token. secret 为空时保持兼容, 不启用校验。"""
    secret = str(secret or "")
    if not secret:
        return True, ""
    bed = str(bed or "").strip()
    token = str(token or "").strip()
    if not bed:
        return False, "缺少 bed 参数"
    if not token:
        return False, "缺少床位访问 token"
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != "v1":
        return False, "床位访问 token 格式无效"
    try:
        expires = int(parts[1])
    except ValueError:
        return False, "床位访问 token 过期时间无效"
    now = time.time() if now is None else float(now)
    if expires < int(now):
        return False, "床位访问 token 已过期"
    expected = _patient_token_signature(secret, bed, expires)
    if not hmac.compare_digest(expected, parts[2]):
        return False, "床位访问 token 不匹配"
    return True, ""


# ============================================================
# 用药说明模板 (mock 数据没拆分医嘱时, 按药品名补)
# 真实接入药房系统后, drug item 字段会从 HIS / EMR 直接拿
# ============================================================

# (匹配关键字 -> 模板字段)
_DRUG_TEMPLATES = [
    (
        ("阿莫西林",),
        {
            "dose": "0.5 g",
            "frequency": "每日 3 次",
            "route": "oral",
            "route_label": "口服",
            "timing": "饭后服用",
            "duration": "连服 5 天",
            "precautions": "对青霉素过敏者禁用; 出现皮疹立即停药并告知护士。",
        },
    ),
    (
        ("布洛芬",),
        {
            "dose": "0.3 g",
            "frequency": "每 12 小时 1 次",
            "route": "oral",
            "route_label": "口服",
            "timing": "随餐",
            "duration": "疼痛缓解后停药",
            "precautions": "胃溃疡患者慎用; 不与其他解热镇痛药合用。",
        },
    ),
    (
        ("头孢", "克肟"),
        {
            "dose": "100 mg",
            "frequency": "每日 2 次",
            "route": "oral",
            "route_label": "口服",
            "timing": "饭后",
            "duration": "连服 7 天",
            "precautions": "服药期间禁酒。",
        },
    ),
    (
        ("降压",),
        {
            "dose": "5 mg",
            "frequency": "每日 1 次",
            "route": "oral",
            "route_label": "口服",
            "timing": "早餐前",
            "duration": "长期",
            "precautions": "定期监测血压, 不可自行停药。",
        },
    ),
    (
        ("维生素",),
        {
            "dose": "100 mg",
            "frequency": "每日 1 次",
            "route": "oral",
            "route_label": "口服",
            "timing": "饭后",
            "duration": "1 个月",
        },
    ),
    (
        ("氯化钠", "葡萄糖", "注射液"),
        {
            "dose": "250 ml",
            "frequency": "每日 1 次",
            "route": "injection_iv",
            "route_label": "静脉滴注",
            "timing": "上午",
            "precautions": "由护士操作, 滴速 60 滴/分钟以下。",
        },
    ),
    (
        ("头孢呋辛",),
        {
            "dose": "1 盒",
            "frequency": "按需",
            "route": "other",
            "route_label": "口服",
            "usage_text": "请按医嘱核对姓名、床位和药品包装后服用。",
        },
    ),
]


def _apply_drug_template(name):
    """按药品名查模板, 返回字段 dict (找不到返回 {})"""
    if not name:
        return {}
    for keywords, fields in _DRUG_TEMPLATES:
        for kw in keywords:
            if kw in name:
                return dict(fields)
    return {}


# ============================================================
# 数据视图转换
# ============================================================

def _ok(data=None):
    if data is None:
        return {"ok": True}
    return {"ok": True, "data": data}


def _err(message):
    return {"ok": False, "error": str(message)}


def _find_mock_patient(bed):
    bed_norm = str(bed).strip()
    for p in PATIENT_MEDICATION_ORDERS:
        if str(p.get("bed_no") or "").strip() == bed_norm:
            return p
    return None


def _patient_profile_from(source):
    """Extract optional patient demographic fields for patient web display."""
    if not isinstance(source, dict):
        return {}
    profile = {}
    field_pairs = (
        ("age", ("age", "patient_age")),
        ("gender", ("gender", "sex", "patient_gender")),
        ("height_cm", ("height_cm", "height", "patient_height_cm")),
        ("weight_kg", ("weight_kg", "weight", "patient_weight_kg")),
    )
    for out_key, keys in field_pairs:
        for key in keys:
            value = source.get(key)
            if value is None or value == "":
                continue
            profile[out_key] = value
            break
    return profile


def _patient_health_context_from(source):
    """Extract clinical context used by patient UI and voice assistant."""
    if not isinstance(source, dict):
        return {}
    context = {}
    field_pairs = (
        ("diagnosis", ("diagnosis", "diagnoses", "primary_diagnosis", "disease", "condition")),
        ("allergies", ("allergies", "allergy", "allergy_history", "drug_allergies")),
        ("contraindications", ("contraindications", "contraindication", "warnings", "avoidance")),
        ("nursing_note", ("nursing_note", "nurse_note", "care_note", "patient_note", "clinical_note")),
    )
    for out_key, keys in field_pairs:
        for key in keys:
            value = source.get(key)
            if value is None or value == "":
                continue
            if isinstance(value, (list, tuple)):
                value = "?".join(str(v).strip() for v in value if str(v).strip())
            else:
                value = str(value).strip()
            if value:
                context[out_key] = value
                break
    return context


def _merge_patient_profile(target, source):
    profile = _patient_profile_from(source)
    if profile:
        target.update(profile)
    health_context = _patient_health_context_from(source)
    if health_context:
        target.update(health_context)
    return target


def _parse_qty(value, default=1):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _split_quantity_unit(value, default_quantity=1, default_unit="盒"):
    raw = str(value or "").strip()
    unit_default = str(default_unit or "盒").strip() or "盒"
    if not raw:
        return default_quantity, unit_default
    match = re.match(r"^\s*(\d+(?:\.\d+)?)\s*([\u4e00-\u9fa5A-Za-z%/μ]+)?\s*$", raw)
    if match:
        quantity = _parse_qty(match.group(1), default=default_quantity)
        unit = (match.group(2) or unit_default).strip()
        return quantity, unit or unit_default
    return _parse_qty(raw, default=default_quantity), unit_default


def _looks_like_pack_unit(value):
    text = str(value or "").strip()
    return bool(re.match(r"^\s*\d+(?:\.\d+)?\s*(盒|片|粒|袋|瓶|支|包|板|份)\s*$", text))


def _looks_like_clinical_dose(value):
    text = str(value or "").strip()
    return bool(re.search(r"\b(mg|g|ml|ug|μg|mcg|iu|IU|mmHg|mmol/L)\b", text)) or bool(re.search(r"毫克|克|毫升|微克|国际单位", text))

def _meds_to_drugs(meds):
    """把 dashboard PATIENT_MEDICATION_ORDERS 或 DeliveryState 里的 medications
    转成前端 DrugItem schema。dashboard mock 的 dose 字段实际上是"包装单位"
    (例如 "1 盒"), usage 是"用法说明"段, 这里做了适配。"""
    out = []
    for m in meds or []:
        name = str(m.get("medicine_name") or m.get("drug_name") or "")
        tpl = _apply_drug_template(name)

        # 外部批次中 quantity 可能是 "1盒"/"2板"；dose 是临床剂量如 "100 mg"。
        # 这里必须把包装数量和临床剂量拆开，避免 8081 显示 unit=100 mg。
        fallback_unit = m.get("unit") or m.get("package_unit") or m.get("pack_unit") or tpl.get("unit") or "盒"
        if not m.get("quantity") and _looks_like_pack_unit(m.get("dose")):
            quantity, unit = _split_quantity_unit(m.get("dose"), default_quantity=1, default_unit=fallback_unit)
        else:
            quantity, unit = _split_quantity_unit(m.get("quantity"), default_quantity=1, default_unit=fallback_unit)
        usage_text = str(m.get("usage") or "")

        item = {
            "drug_id": str(m.get("id") or m.get("product_code") or ""),
            "drug_name": name,
            "quantity": quantity,
            "unit": unit,
        }
        # 模板补字段 (mock 没拆分时)
        # 注意: 旧 mock 的 "dose" 若是 "1盒" 会被当包装单位；外部批次的 "100 mg" 会作为临床剂量。
        for k in (
            "frequency",
            "route",
            "route_label",
            "timing",
            "duration",
            "precautions",
            "doctor_note",
        ):
            v = m.get(k) or tpl.get(k)
            if v:
                item[k] = str(v)
        real_dose = m.get("dose_clinical") or m.get("strength")
        raw_dose = m.get("dose")
        if raw_dose and _looks_like_clinical_dose(raw_dose):
            real_dose = raw_dose
        dose_val = real_dose or tpl.get("dose")
        if dose_val:
            item["dose"] = str(dose_val)

        # 如果有 usage 文本(且没拆到 frequency/precautions), 给 usage_text
        if usage_text and not item.get("frequency"):
            item["usage_text"] = usage_text
        elif tpl.get("usage_text"):
            item["usage_text"] = tpl["usage_text"]

        out.append(item)
    return out


def _drugs_summary(drugs):
    if not drugs:
        return ""
    first = drugs[0]
    name = first.get("drug_name") or ""
    qty = first.get("quantity")
    extra = f" 等 {len(drugs)} 项" if len(drugs) > 1 else ""
    if qty:
        return f"{name} ×{qty}{extra}".strip()
    return f"{name}{extra}".strip()


def _make_delivery_id(bed):
    return f"PWB-{bed}-{datetime.now().strftime('%Y%m%d')}"


_ORDER_ID_BED_RE = re.compile(r"^PWB-(.+)-\d{8}(?:-\d+)?$")


def _bed_from_delivery_id(delivery_id):
    """delivery_id 形如 PWB-{bed}-20260611(-001), bed 内部可以包含 dash"""
    m = _ORDER_ID_BED_RE.match(str(delivery_id))
    if m:
        return m.group(1)
    return ""


# ============================================================
# 当前派送视图
# ============================================================

# 兜底的处方/医生信息, 真实数据来自 EMR
_DEFAULT_DOCTOR = {"name": "李慧敏", "title": "副主任医师"}
_DEFAULT_PRESCRIPTION_NOTE = (
    "如出现皮疹、恶心或不适, 请立即告知护士; 服药期间避免饮酒。"
)


_BED_SPLIT_RE = re.compile(r"[、,，;；\s]+")


def _state_bed_list(state):
    """task_manager 批次任务时 bed_no 形如 'A-01、A-02', 拆开"""
    raw = str(state.get("bed_no") or "").strip()
    if not raw:
        return []
    return [b.strip() for b in _BED_SPLIT_RE.split(raw) if b.strip()]


def _patient_name_for_bed(state, bed, meds=None):
    """批次场景下 patient_name 形如 '张三、王五', 按位置和 bed_list 对齐拿"""
    beds = _state_bed_list(state)
    names_raw = str(state.get("patient_name") or "").strip()
    if beds and names_raw:
        names = [n.strip() for n in _BED_SPLIT_RE.split(names_raw) if n.strip()]
        if len(names) == len(beds):
            for b, n in zip(beds, names):
                if b == bed:
                    return n
    # 兜底: 从 meds 里找
    for m in meds or []:
        if str(m.get("bed_no") or "").strip() == str(bed).strip():
            n = str(m.get("patient_name") or "").strip()
            if n:
                return n
    # 单床任务直接拿顶层
    return names_raw


def _build_from_delivery_state(state, bed=""):
    """从 DeliveryState 字典构造 PatientDelivery schema (best effort).
    注意: latest_state 的状态字段是 'state' (来自 DeliveryState.msg state 字段),
    历史上写成 'status' 是个 bug, 现已修正。

    bed: 如果传入, 则在批次场景下过滤药品 (medications_json 里每条带 bed_no)
    并用该 bed 对应的 patient_name."""
    task_id = str(state.get("task_id") or state.get("active_task_id") or "")
    # task_manager 真实推送的状态在 'state' 字段; 'status'/'phase' 是兼容旧调用方
    status_raw = str(
        state.get("state") or state.get("status") or state.get("phase") or ""
    ).lower()
    status = _STATUS_MAP.get(status_raw, "prescribed")
    eta = state.get("eta_seconds")
    if eta is None and status == "delivering":
        eta = 300
    # 真实 state.medications_json 是 JSON 字符串, 需要 parse
    meds = state.get("medications") or state.get("drugs") or []
    if not meds:
        meds_json = state.get("medications_json")
        if meds_json:
            try:
                import json as _json
                parsed = _json.loads(meds_json)
                if isinstance(parsed, list):
                    meds = parsed
            except Exception:
                pass
    # 没拆分的情况下, 至少用顶层 medicine_name + quantity 拼一条
    if not meds and state.get("medicine_name"):
        meds = [
            {
                "medicine_name": state.get("medicine_name"),
                "quantity": state.get("quantity") or "1",
                "product_code": state.get("product_code") or "",
                "trace_id": state.get("trace_id") or "",
            }
        ]
    # 批次场景: 只挑当前床位的药 (DeliveryState.medications_json 里每条带 bed_no)
    bed_norm = str(bed or "").strip()
    if bed_norm and meds:
        filtered = [m for m in meds if str(m.get("bed_no") or "").strip() == bed_norm]
        if filtered:
            meds = filtered

    patient_name = _patient_name_for_bed(state, bed_norm, meds) if bed_norm else (
        state.get("patient_name") or ""
    )
    bed_field = bed_norm or state.get("bed_no") or ""

    payload = {
        "delivery_id": task_id or f"DLV-{int(time.time())}",
        "bed": bed_field,
        "patient_name": patient_name,
        "ward": state.get("ward_name") or state.get("ward_id") or "",
        "status": status,
        "drugs": _meds_to_drugs(meds),
        "dispatched_at": state.get("created_at") or datetime.now().isoformat(),
        "eta_seconds": eta,
        "doctor_name": state.get("doctor_name") or _DEFAULT_DOCTOR["name"],
        "doctor_title": state.get("doctor_title")
        or _DEFAULT_DOCTOR["title"],
        "prescription_no": state.get("prescription_no")
        or state.get("order_no")
        or "",
        "prescription_note": state.get("prescription_note")
        or _DEFAULT_PRESCRIPTION_NOTE,
    }
    _merge_patient_profile(payload, state)
    return payload


def _build_from_delivery_batch(dashboard, bed):
    """从当前 DeliveryBatch 中按床位构造 8081 PatientDelivery。外部批次采用后，B-01/C-01 可直接查询。"""
    bed_norm = str(bed or "").strip()
    if not bed_norm:
        return None
    batch = getattr(dashboard, "delivery_batch", None) or {}
    if not isinstance(batch, dict):
        return None
    for stop in batch.get("stops", []) or []:
        if not isinstance(stop, dict):
            continue
        for patient in stop.get("patients", []) or []:
            if not isinstance(patient, dict):
                continue
            if str(patient.get("bed_no") or "").strip() != bed_norm:
                continue
            status = "prescribed"
            patient_status = str(patient.get("patient_status") or "").upper()
            route_status = str(batch.get("route_status") or "").upper()
            stop_status = str(stop.get("stop_status") or "").upper()
            if patient_status == "COMPLETED":
                status = "confirmed"
            elif patient_status == "MEDICATION_RETURNED_FOR_REVIEW":
                status = "rejected"
            elif patient_status == "WAITING_MEDICATION_REVIEW" or patient.get("medication_review_required"):
                status = "review"
            elif patient_status in {"PATIENT_ABSENT", "EXCEPTION"}:
                status = "rejected"
            elif route_status == "NAVIGATING_TO_WARD" or stop_status == "NAVIGATING_TO_WARD":
                status = "delivering"
            elif route_status == "WARD_HANDOVER" or stop_status == "WARD_HANDOVER":
                status = "arrived"
            meds = []
            for med in patient.get("medications", []) or []:
                if not isinstance(med, dict):
                    continue
                m = dict(med)
                m.setdefault("bed_no", bed_norm)
                m.setdefault("patient_name", patient.get("patient_name") or "")
                meds.append(m)
            return {
                "delivery_id": str(batch.get("batch_id") or _make_delivery_id(bed_norm)),
                "bed": bed_norm,
                "patient_name": patient.get("patient_name") or "",
                "ward": patient.get("ward_name") or stop.get("display_name") or patient.get("ward_id") or stop.get("target_station") or "",
                **_patient_profile_from(patient),
                **_patient_health_context_from(patient),
                "status": status,
                "medication_review_resolution": patient.get("medication_review_resolution") or "",
                "medication_review_resolved_at": patient.get("medication_review_resolved_at") or "",
                "medication_review_resolution_reason": patient.get("medication_review_resolution_reason") or "",
                "medication_review_reason": patient.get("medication_review_reason") or "",
                "drugs": _meds_to_drugs(meds),
                "dispatched_at": batch.get("created_time") or batch.get("issued_at") or datetime.now().isoformat(),
                "eta_seconds": None,
                "doctor_name": patient.get("doctor_name") or _DEFAULT_DOCTOR["name"],
                "doctor_title": patient.get("doctor_title") or _DEFAULT_DOCTOR["title"],
                "prescription_no": patient.get("prescription_no") or "",
                "prescription_note": patient.get("prescription_note") or _DEFAULT_PRESCRIPTION_NOTE,
            }
    return None

def build_current_delivery(dashboard, bed):
    """优先 latest_state, 否则 PATIENT_MEDICATION_ORDERS + override.

    无论走哪条分支, 都要让 patient_status_overrides 中的终态/超时枚举覆盖
    task_manager 推送出来的 status——否则病人在 WAITING_DISPENSE_CONFIRMATION
    阶段点 confirm 后, /patient/api/delivery 仍会从 latest_state 映射出
    'arrived', UI 卡在"已到达床旁"直到 task_manager 推下一个状态。
    """
    state = getattr(dashboard, "latest_state", {}) or {}
    # 单床: state.bed_no == bed; 批次: state.bed_no = "A-01、A-02" 包含 bed
    bed_list = _state_bed_list(state)
    bed_norm = str(bed).strip()
    overrides = getattr(dashboard, "patient_status_overrides", {}) or {}
    ovr = overrides.get(bed_norm) if bed_norm else None

    if state.get("task_id") and (
        (not bed_list and str(state.get("bed_no") or "").strip() == bed_norm)
        or bed_norm in bed_list
    ):
        result = _build_from_delivery_state(state, bed_norm)
        # override 优先: 病人已 confirm/reject 或后端打了 timeout 标签时,
        # task_manager 状态机映射应让位 (与 _api_robot_status overlay 对齐)
        if ovr:
            ovr_status = ovr.get("status")
            if ovr_status in {"confirmed", "rejected", "timeout", "review"} and ovr_status in _VALID_PATIENT_STATUSES:
                result["status"] = ovr_status
        return result

    batch_delivery = _build_from_delivery_batch(dashboard, bed_norm)
    if batch_delivery is not None:
        if ovr:
            ovr_status = ovr.get("status")
            if ovr_status in {"confirmed", "rejected", "timeout", "review"} and ovr_status in _VALID_PATIENT_STATUSES:
                batch_delivery["status"] = ovr_status
        return batch_delivery

    mock = _find_mock_patient(bed)
    if mock is None:
        return None

    info = overrides.get(bed, {"status": "prescribed", "eta": None})
    # 白名单: _STATUS_MAP 的 value 集 (task_manager 推送链) + override 链允许的扩展枚举
    # 任何不在此集的 status 一律 fallback 到 'prescribed', 避免前端 STATUS_META[未知] 取 .icon 整页崩
    raw_status = info.get("status", "prescribed")
    if raw_status not in _VALID_PATIENT_STATUSES:
        status_out = "prescribed"
    else:
        status_out = raw_status
    return {
        "delivery_id": _make_delivery_id(bed),
        "bed": bed,
        "patient_name": mock.get("patient_name") or "",
        "ward": mock.get("ward_name") or mock.get("ward_id") or "",
        **_patient_profile_from(mock),
        **_patient_health_context_from(mock),
        "status": status_out,
        "drugs": _meds_to_drugs(mock.get("medications")),
        "dispatched_at": datetime.now().isoformat(),
        "eta_seconds": info.get("eta"),
        "doctor_name": _DEFAULT_DOCTOR["name"],
        "doctor_title": _DEFAULT_DOCTOR["title"],
        "prescription_no": (mock.get("medications") or [{}])[0].get("order_no")
        or "",
        "prescription_note": _DEFAULT_PRESCRIPTION_NOTE,
    }


def build_patient_identity(dashboard, bed):
    delivery = build_current_delivery(dashboard, bed)
    if delivery is None:
        return None
    return {
        "bed": delivery.get("bed") or bed,
        "ward": delivery.get("ward") or "",
        "patient_name": delivery.get("patient_name") or "",
        "age": delivery.get("age") or "",
        "gender": delivery.get("gender") or "",
        "height_cm": delivery.get("height_cm") or "",
        "weight_kg": delivery.get("weight_kg") or "",
        "diagnosis": delivery.get("diagnosis") or "",
        "allergies": delivery.get("allergies") or "",
        "contraindications": delivery.get("contraindications") or "",
        "nursing_note": delivery.get("nursing_note") or "",
        "has_delivery": bool(delivery.get("delivery_id")),
        "delivery_id": delivery.get("delivery_id") or "",
    }


# ============================================================
# 历史
# ============================================================

def _normalize_batch_status(b):
    s = str(b.get("status") or b.get("result") or "").lower()
    if s in ("ok", "success", "completed", "confirmed", "done"):
        return "confirmed"
    if s in ("rejected", "patient_reject"):
        return "rejected"
    if s in ("cancelled", "canceled"):
        return "cancelled"
    return "confirmed"


def _parse_iso_ts(value):
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except Exception:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


def build_history(dashboard, bed, days=7):
    out = []
    cutoff = time.time() - max(1, int(days)) * 86400
    try:
        with dashboard.delivery_db_lock:
            batches = (
                dashboard.delivery_db.get_recent_batches(limit=80)
                if dashboard.delivery_db
                else []
            )
    except Exception as exc:
        dashboard.get_logger().warn(
            f"[patient_web] history db query failed: {exc}"
        )
        batches = []

    for b in batches:
        try:
            ts = _parse_iso_ts(b.get("created_at") or b.get("timestamp"))
            if ts and ts < cutoff:
                continue
            patient = b.get("patient_data") or b.get("patient") or {}
            if str(patient.get("bed_no") or "") != str(bed):
                continue
            date_label = (
                datetime.fromtimestamp(ts).strftime("%m/%d %H:%M") if ts else ""
            )
            meds = patient.get("medications") or b.get("medications") or []
            drugs_dto = _meds_to_drugs(meds)
            out.append(
                {
                    "delivery_id": str(b.get("batch_id") or b.get("id") or ""),
                    "date": date_label,
                    "drugs_summary": _drugs_summary(drugs_dto),
                    "status": _normalize_batch_status(b),
                    "drugs": drugs_dto,
                }
            )
        except Exception:
            continue

    # 加上内存中的 self-service log
    for h in getattr(dashboard, "patient_history_log", []):
        if h.get("bed") != bed:
            continue
        out.append(
            {
                "delivery_id": h["delivery_id"],
                "date": h["date"],
                "drugs_summary": h["drugs_summary"],
                "status": h["status"],
            }
        )

    seen = set()
    uniq = []
    for e in out:
        key = e["delivery_id"]
        if key in seen:
            continue
        seen.add(key)
        uniq.append(e)
    return uniq


def _build_voice_patient_context(dashboard, bed, delivery_id=""):
    delivery = build_current_delivery(dashboard, bed)
    if not isinstance(delivery, dict):
        delivery = {}
    drugs = []
    for item in delivery.get("drugs") or []:
        if not isinstance(item, dict):
            continue
        drugs.append(
            {
                "drug_name": item.get("drug_name") or item.get("medicine_name") or "",
                "dose": item.get("dose") or "",
                "frequency": item.get("frequency") or "",
                "route_label": item.get("route_label") or "",
                "timing": item.get("timing") or "",
                "duration": item.get("duration") or "",
                "precautions": item.get("precautions") or "",
                "doctor_note": item.get("doctor_note") or "",
                "usage_text": item.get("usage_text") or "",
                "quantity": item.get("quantity") or "",
                "unit": item.get("unit") or "",
            }
        )
    return {
        "source": "patient_web",
        "bed": str(bed or ""),
        "delivery_id": str(delivery_id or delivery.get("delivery_id") or ""),
        "patient_name": delivery.get("patient_name") or "",
        "ward": delivery.get("ward") or "",
        "status": delivery.get("status") or "",
        "doctor_name": delivery.get("doctor_name") or "",
        "doctor_title": delivery.get("doctor_title") or "",
        "prescription_no": delivery.get("prescription_no") or "",
        "prescription_note": delivery.get("prescription_note") or "",
        "age": delivery.get("age") or "",
        "gender": delivery.get("gender") or "",
        "height_cm": delivery.get("height_cm") or "",
        "weight_kg": delivery.get("weight_kg") or "",
        "diagnosis": delivery.get("diagnosis") or "",
        "allergies": delivery.get("allergies") or "",
        "contraindications": delivery.get("contraindications") or "",
        "nursing_note": delivery.get("nursing_note") or "",
        "drugs": drugs,
        "safety_rules": [
            "只能解释当前医嘱和药品注意事项，不能修改剂量、停药或换药。",
            "遇到过敏、呼吸困难、胸痛、大出血、意识不清等危险情况，提示立即联系护士或医生。",
            "孕妇、儿童、老人、肝肾功能异常等复杂用药，提示以医生或药师确认为准。",
        ],
        "created_at": time.time(),
    }
# ============================================================
# 状态 override + service 调用
# ============================================================

def _set_status_override(dashboard, delivery_id, status, bed="", reason=""):
    """记 override + 加 history. bed 优先从 body, 否则从 delivery_id 反推"""
    if not bed:
        bed = _bed_from_delivery_id(delivery_id)
    dashboard.patient_status_overrides[bed] = {
        "status": status,
        "eta": None,
        "reason": reason,
    }
    drugs_summary = "病人确认收到" if status == "confirmed" else "病人反馈问题"
    if reason:
        drugs_summary = f"{drugs_summary} ({reason})"
    history_entry = {
        "delivery_id": delivery_id,
        "bed": bed,
        "date": datetime.now().strftime("%m/%d %H:%M"),
        "drugs_summary": drugs_summary,
        "status": status,
    }
    dashboard.patient_history_log.insert(0, history_entry)
    if len(dashboard.patient_history_log) > 50:
        del dashboard.patient_history_log[50:]
    # 持久化 (断电恢复用); 失败不影响内存视图
    store = getattr(dashboard, "patient_state_store", None)
    if store is not None:
        try:
            store.upsert_override(bed, status, reason or "", delivery_id or "")
            store.insert_history(history_entry)
        except Exception as exc:
            try:
                dashboard.get_logger().warn(
                    f"[patient_web] persist override/history failed: {exc}"
                )
            except Exception:
                pass



def _is_medication_review_message(content):
    text = str(content or "")
    markers = (
        "\u75c5\u4eba\u7aef\u53cd\u9988",
        "\u4fe1\u606f\u6709\u8bef",
        "\u7528\u836f",
        "\u836f\u54c1",
        "\u5242\u91cf",
        "\u8fc7\u654f",
        "\u6838\u5bf9",
    )
    return any(m in text for m in markers)


def _set_review_override_from_message(dashboard, delivery_id, bed, content):
    reason = "\u75c5\u4eba\u53cd\u9988\u7528\u836f\u6216\u4e2a\u4eba\u4fe1\u606f\u53ef\u80fd\u6709\u8bef\uff0c\u5f85\u62a4\u58eb\u590d\u6838"
    _set_status_override(dashboard, delivery_id, "review", bed=bed, reason=reason)
    if hasattr(dashboard, "mark_patient_medication_review_required"):
        try:
            return dashboard.mark_patient_medication_review_required(
                bed=bed,
                delivery_id=delivery_id,
                reason=reason,
                source="patient_message",
            )
        except Exception as exc:
            try:
                dashboard.get_logger().warn(f"[patient_web] mark review required failed: {exc}")
            except Exception:
                pass
    return {"ok": False, "message": "review marker unavailable"}


def _try_verify(dashboard, delivery_id, stage, note=""):
    """尽力调用 verify_delivery_task service, 失败也不阻断 patient UI"""
    try:
        from medicine_interfaces.srv import VerifyDeliveryTask
    except Exception:
        return False
    client = getattr(dashboard, "verify_task_client", None)
    if client is None:
        return False
    try:
        if not client.wait_for_service(timeout_sec=0.5):
            return False
        req = VerifyDeliveryTask.Request()
        req.task_id = str(delivery_id)
        if hasattr(req, "stage"):
            req.stage = stage
        client.call_async(req)
        if note:
            dashboard.get_logger().info(
                f"[patient_web] verify {stage} task={delivery_id} note={note}"
            )
        return True
    except Exception as exc:
        dashboard.get_logger().warn(
            f"[patient_web] verify call failed: {exc}"
        )
        return False


# ============================================================
# Handler factory
# ============================================================

def create_patient_handler(dashboard, dist_dir):
    # 注: dashboard 在 __init__ 里已经把这两个字段初始化好了 (并已从 SQLite 回灌)
    # 这里只做防御性保护, 不要再 = {} 把恢复的数据冲掉
    if not hasattr(dashboard, "patient_status_overrides") or dashboard.patient_status_overrides is None:
        dashboard.patient_status_overrides = {}
    if not hasattr(dashboard, "patient_history_log") or dashboard.patient_history_log is None:
        dashboard.patient_history_log = []

    dist_root = os.path.realpath(dist_dir)

    class PatientHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *args):
            status = int(args[1]) if len(args) > 1 and str(args[1]).isdigit() else 0
            if status < 400:
                return
            try:
                dashboard.get_logger().warn("[patient_web] " + (fmt % args))
            except Exception:
                pass

        # ----- 响应工具 -----
        def _send_json(self, body, status=200):
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            self.wfile.write(payload)

        def _access_secret(self):
            return str(getattr(dashboard, "patient_access_secret", "") or "")

        def _extract_access_token(self, params=None, body=None):
            params = params or {}
            body = body or {}
            from_query = (
                (params.get("t") or params.get("token") or [""])[0]
                if isinstance(params, dict)
                else ""
            )
            from_body = (
                body.get("t")
                or body.get("token")
                or body.get("patient_token")
                or ""
            )
            from_header = self.headers.get("X-Patient-Token", "")
            return str(from_query or from_body or from_header or "").strip()

        def _authorize_bed_access(self, bed, params=None, body=None):
            ok, reason = verify_patient_access_token(
                self._access_secret(),
                bed,
                self._extract_access_token(params=params, body=body),
            )
            if ok:
                return True
            self._send_json(_err(reason), 403)
            return False

        def _send_redirect(self, target):
            self.send_response(302)
            self.send_header("Location", target)
            self.send_header("Connection", "keep-alive")
            self.end_headers()

        def _send_text(self, text, status=200, ctype="text/plain"):
            body = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", f"{ctype}; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            self.wfile.write(body)

        def _send_file(self, path):
            try:
                with open(path, "rb") as f:
                    body = f.read()
            except OSError:
                self._send_text("Not found", 404)
                return
            ctype, _ = mimetypes.guess_type(path)
            encoding = ""
            accept_encoding = self.headers.get("Accept-Encoding", "")
            if (
                "gzip" in accept_encoding.lower()
                and path.endswith((".js", ".css", ".html", ".json", ".svg"))
                and len(body) > 1024
            ):
                body = gzip.compress(body, compresslevel=6)
                encoding = "gzip"
            self.send_response(200)
            self.send_header(
                "Content-Type", ctype or "application/octet-stream"
            )
            if encoding:
                self.send_header("Content-Encoding", encoding)
                self.send_header("Vary", "Accept-Encoding")
            self.send_header("Content-Length", str(len(body)))
            self.send_header(
                "Cache-Control",
                "no-cache"
                if path.endswith((".html", ".json"))
                else "public, max-age=86400",
            )
            self.send_header("Connection", "close")
            self.close_connection = True
            self.end_headers()
            self.wfile.write(body)

        def _read_body(self):
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except (TypeError, ValueError):
                length = 0
            limit = getattr(dashboard, "max_request_body_bytes", 262144)
            length = max(0, min(length, limit))
            if length == 0:
                return {}
            raw = self.rfile.read(length)
            try:
                return json.loads(raw.decode("utf-8"))
            except Exception:
                return {}

        # ----- 静态 -----
        def _serve_static(self, raw_path):
            sub = raw_path[len(_BASE_PATH):]
            sub = unquote(sub)
            if sub in ("", "/"):
                sub = "index.html"
            if "\0" in sub or sub.startswith("/") or ".." in sub.split("/"):
                self._send_text("Bad path", 400)
                return
            candidate = os.path.realpath(os.path.join(dist_root, sub))
            if not candidate.startswith(dist_root):
                self._send_text("Bad path", 400)
                return
            if os.path.isfile(candidate):
                self._send_file(candidate)
                return
            index = os.path.join(dist_root, "index.html")
            if os.path.isfile(index):
                self._send_file(index)
                return
            self._send_text(
                f"patient_web 未部署: 请把 dist/ 同步到 {dist_root}",
                404,
            )

        # ----- API -----
        def _api_delivery(self, params):
            bed = (params.get("bed") or [""])[0].strip()
            if not bed:
                self._send_json(_err("缺少 bed 参数"), 400)
                return
            if not self._authorize_bed_access(bed, params=params):
                return
            self._send_json(_ok(build_current_delivery(dashboard, bed)))

        def _api_identity(self, params):
            bed = (params.get("bed") or [""])[0].strip()
            if not bed:
                self._send_json(_err("缺少 bed 参数"), 400)
                return
            if not self._authorize_bed_access(bed, params=params):
                return
            identity = build_patient_identity(dashboard, bed)
            if identity is None:
                self._send_json(_err("未找到该病房床号的登记信息"), 404)
                return
            self._send_json(_ok(identity))

        def _api_history(self, params):
            bed = (params.get("bed") or [""])[0].strip()
            if not bed:
                self._send_json(_err("缺少 bed 参数"), 400)
                return
            if not self._authorize_bed_access(bed, params=params):
                return
            try:
                days = int((params.get("days") or ["7"])[0])
            except (TypeError, ValueError):
                days = 7
            self._send_json(_ok(build_history(dashboard, bed, days=days)))

        def _api_confirm(self, delivery_id, body):
            bed = str(body.get("bed") or "").strip()
            if not bed:
                bed = _bed_from_delivery_id(delivery_id)
            if not self._authorize_bed_access(bed, body=body):
                return
            _set_status_override(
                dashboard, delivery_id, "confirmed", bed=bed
            )
            verified = _try_verify(dashboard, delivery_id, "patient_confirm")
            batch_recorded = False
            batch_message = ""
            if hasattr(dashboard, "record_patient_receipt_in_batch"):
                try:
                    batch_response = dashboard.record_patient_receipt_in_batch(
                        delivery_id, bed, "confirmed"
                    )
                    batch_recorded = bool(batch_response.get("ok"))
                    batch_message = str(batch_response.get("message") or "")
                except Exception as exc:
                    batch_message = str(exc)
                    try:
                        dashboard.get_logger().warn(
                            f"[patient_web] record patient receipt failed: {exc}"
                        )
                    except Exception:
                        pass
            # 闭环 A: 在该床位 IM 会话里写一条系统消息, 让医护立刻看到
            if bed:
                try:
                    dashboard.append_system_message(
                        bed=bed,
                        content=f"病人已确认收到该次药品 (派送 {delivery_id})",
                        delivery_id=delivery_id,
                    )
                except Exception:
                    pass
            self._send_json(
                _ok(
                    {
                        "delivery_id": delivery_id,
                        "bed": bed,
                        "verified": verified,
                        "batch_recorded": batch_recorded,
                        "batch_message": batch_message,
                    }
                )
            )

        def _api_reject(self, delivery_id, body):
            bed = str(body.get("bed") or "").strip()
            if not bed:
                bed = _bed_from_delivery_id(delivery_id)
            if not self._authorize_bed_access(bed, body=body):
                return
            reason = str(body.get("reason") or "")[:200]
            _set_status_override(
                dashboard, delivery_id, "rejected", bed=bed, reason=reason
            )
            _try_verify(dashboard, delivery_id, "patient_reject", note=reason)
            batch_recorded = False
            batch_message = ""
            if hasattr(dashboard, "record_patient_receipt_in_batch"):
                try:
                    batch_response = dashboard.record_patient_receipt_in_batch(
                        delivery_id, bed, "rejected", reason=reason
                    )
                    batch_recorded = bool(batch_response.get("ok"))
                    batch_message = str(batch_response.get("message") or "")
                except Exception as exc:
                    batch_message = str(exc)
                    try:
                        dashboard.get_logger().warn(
                            f"[patient_web] record patient reject failed: {exc}"
                        )
                    except Exception:
                        pass
            # 闭环 A: 在该床位 IM 会话里写一条系统消息(标红), 让医护立刻看到病人反馈
            if bed:
                try:
                    reason_txt = reason or "未填写原因"
                    dashboard.append_system_message(
                        bed=bed,
                        content=f"⚠️ 病人反馈问题/拒绝收药: {reason_txt} (派送 {delivery_id})",
                        delivery_id=delivery_id,
                    )
                except Exception:
                    pass
            self._send_json(
                _ok(
                    {
                        "delivery_id": delivery_id,
                        "bed": bed,
                        "reason": reason,
                        "batch_recorded": batch_recorded,
                        "batch_message": batch_message,
                    }
                )
            )

        def _api_call_robot(self, body):
            bed = str(body.get("bed") or "").strip()
            reason = str(body.get("reason") or "")[:200]
            if not bed:
                self._send_json(_err("缺少 bed"), 400)
                return
            if not self._authorize_bed_access(bed, body=body):
                return
            try:
                from std_msgs.msg import String as _String

                msg = _String()
                msg.data = json.dumps(
                    {
                        "bed": bed,
                        "reason": reason,
                        "timestamp": datetime.now().isoformat(),
                        "source": "patient_web",
                    },
                    ensure_ascii=False,
                )
                dashboard.patient_call_publisher.publish(msg)
                dashboard.get_logger().info(
                    f"[patient_web] call_robot bed={bed} reason={reason!r}"
                )
            except Exception as exc:
                self._send_json(_err(f"发布失败: {exc}"), 500)
                return
            self._send_json(_ok({"queued": True, "bed": bed}))

        def _api_robot_status(self, params):
            """闭环 C: 病人端看机器人在哪 + 状态.
            返回当前机器人位置/状态/任务目标, 以及跟该床位是否相关."""
            bed = (params.get("bed") or [""])[0].strip()
            if not self._authorize_bed_access(bed, params=params):
                return
            state = {}
            try:
                state = dashboard.get_state() or {}
            except Exception:
                state = {}
            chassis = {}
            try:
                chassis = dashboard.get_chassis_status() or {}
            except Exception:
                chassis = {}
            current_station = str(state.get("current_station") or "")
            target_station = str(state.get("target_station") or "")
            task_state = str(state.get("state") or "IDLE")
            task_bed = str(state.get("bed_no") or "")
            # 用 patient_status_overrides 看本床是否已 confirmed/rejected
            ovr_all = getattr(dashboard, "patient_status_overrides", {}) or {}
            ovr_bed = ovr_all.get(bed) if bed else None
            # 站点中文名
            station_names = {
                "pharmacy": "药房",
                "ward_a": "A病房",
                "ward_b": "B病房",
                "ward_c": "C病房",
                "": "",
            }
            current_name = station_names.get(current_station, current_station or "未知位置")
            target_name = station_names.get(target_station, target_station)
            # 推断这台机器人现在跟"我"什么关系
            #   for_me = 这次任务的目标床位 == 我
            #   stage: idle / loading / on_the_way / arrived_to_me / arrived_other / done
            # 批次任务 bed_no 形如 "A-01、A-02", 需要拆开看
            task_bed_list = _state_bed_list(state)
            for_me = bool(bed) and (
                task_bed == bed
                or (str(bed).strip() in task_bed_list)
            )
            stage = "idle"
            human_text = "机器人在药房待命"
            # task_manager 真实状态机:
            #   IDLE / WAITING_LOAD_CONFIRMATION / NAVIGATING /
            #   WAITING_DISPENSE_CONFIRMATION / COMPLETED / NAVIGATION_FAILED
            if task_state in (
                "WAITING_LOAD_CONFIRMATION",
                # 兼容历史命名
                "LOAD_AT_PHARMACY", "LOADING", "PHARMACY_LOAD",
            ):
                stage = "loading"
                human_text = "机器人正在药房装药"
            elif task_state in (
                "NAVIGATING",
                # 兼容历史命名
                "MOVING", "DELIVERING", "GO_TO_TARGET",
            ):
                if for_me:
                    stage = "on_the_way_to_me"
                    human_text = "机器人正在送您的药品 · 即将到达"
                else:
                    stage = "on_the_way_other"
                    human_text = f"机器人正在前往 {target_name or '其他病房'}"
            elif task_state in (
                "WAITING_DISPENSE_CONFIRMATION",
                # 兼容历史命名
                "ARRIVED", "AT_TARGET", "WAITING_CONFIRM",
            ):
                if for_me:
                    stage = "arrived_to_me"
                    human_text = "机器人已到达您的床位旁"
                else:
                    stage = "arrived_other"
                    human_text = f"机器人已到达 {target_name or '其他病房'}"
            elif task_state in ("RETURN", "RETURNING", "GO_BACK"):
                stage = "returning"
                human_text = "机器人返航中"
            elif task_state in ("COMPLETED", "DONE", "FINISHED"):
                stage = "done"
                human_text = "本次配送已完成"
            elif task_state == "NAVIGATION_FAILED":
                stage = "idle"
                human_text = "导航异常, 工作人员正在处理"
            # 如果本床位已确认/拒绝/超时, 覆盖 stage
            if ovr_bed and ovr_bed.get("status") == "confirmed":
                stage = "done"
                human_text = "您已确认收药"
            elif ovr_bed and ovr_bed.get("status") == "rejected":
                stage = "done"
                human_text = "您已反馈问题, 已生成护士端复核提醒"
            elif ovr_bed and ovr_bed.get("status") == "timeout":
                # 让 stage 维持 arrived_to_me 以便病人继续点确认; UI 只提示已生成护士端提醒
                stage = "arrived_to_me"
                human_text = "机器人已到位较久, 已生成护士端提醒"
            chassis_ok = bool(chassis.get("ok", True)) if chassis else True
            payload = {
                "bed": bed,
                "task_id": state.get("task_id") or "",
                "task_state": task_state,
                "task_bed": task_bed,
                "current_station": current_station,
                "current_station_name": current_name,
                "target_station": target_station,
                "target_station_name": target_name,
                "for_me": for_me,
                "stage": stage,
                "human_text": human_text,
                "chassis_ok": chassis_ok,
                "battery": chassis.get("battery") or chassis.get("battery_percent"),
                "stamp": time.time(),
            }
            self._send_json(_ok(payload))

        def _api_messages_get(self, params):
            bed = (params.get("bed") or [""])[0].strip()
            if not bed:
                self._send_json(_err("缺少 bed 参数"), 400)
                return
            if not self._authorize_bed_access(bed, params=params):
                return
            mark_read = (params.get("mark_read") or ["1"])[0].strip().lower()
            # 病人打开会话时才把该床位护士回复标记为已读;
            # 底部"咨询护士"按钮轮询未读数时会传 mark_read=0, 避免红点被查询动作清掉。
            if mark_read not in {"0", "false", "no"}:
                try:
                    dashboard.mark_thread_read_by_patient(bed)
                except Exception:
                    pass
            items = dashboard.get_patient_messages(bed=bed)
            self._send_json(_ok({"bed": bed, "messages": items}))

        def _api_voice_listen(self, body):
            bed = str(body.get("bed") or "").strip()
            if bed and not self._authorize_bed_access(bed, body=body):
                return
            try:
                duration = int(body.get("duration_sec") or body.get("duration") or 300)
            except (TypeError, ValueError):
                duration = 300
            duration = max(10, min(300, duration))
            try:
                context_result = {"ok": False}
                if bed and hasattr(dashboard, "publish_patient_voice_context"):
                    context_payload = _build_voice_patient_context(
                        dashboard,
                        bed,
                        delivery_id=str(body.get("delivery_id") or ""),
                    )
                    context_result = dashboard.publish_patient_voice_context(context_payload)
                result = dashboard.start_voice_listen({"duration_sec": duration})
                result["patient_context"] = context_result
                # ???????????, ?????????????? 8085
                try:
                    dashboard.get_logger().info(
                        f"[patient_web] voice_listen bed={bed!r} duration={duration}s "
                        f"context_ok={bool(context_result.get('ok')) if isinstance(context_result, dict) else False}"
                    )
                except Exception:
                    pass
                self._send_json(_ok(result))
            except Exception as exc:
                self._send_json(_err(f"语音监听开启失败: {exc}"), 500)
        def _api_voice_announce(self, body):
            bed = str(body.get("bed") or "").strip()
            if bed and not self._authorize_bed_access(bed, body=body):
                return
            text = str(
                body.get("text")
                or body.get("message")
                or body.get("content")
                or ""
            ).strip()
            if not text:
                self._send_json(_err("\u7f3a\u5c11\u64ad\u62a5\u6587\u672c"), 400)
                return
            # ????????, ?? TTS ?????????
            if len(text) > 260:
                text = text[:260] + "\u3002\u540e\u7eed\u5185\u5bb9\u8bf7\u67e5\u770b\u9875\u9762\u6587\u5b57\u8bf4\u660e\u3002"
            try:
                result = dashboard.announce_voice_text({"text": text})
                self._send_json(_ok(result))
            except Exception as exc:
                self._send_json(_err(f"\u64ad\u62a5\u5931\u8d25: {exc}"), 500)

        def _api_messages_post(self, body):
            bed = str(body.get("bed") or "").strip()
            content = str(body.get("content") or "").strip()
            delivery_id = str(body.get("delivery_id") or "").strip()
            if not bed:
                self._send_json(_err("缺少 bed"), 400)
                return
            if not self._authorize_bed_access(bed, body=body):
                return
            if not content:
                self._send_json(_err("留言内容不能为空"), 400)
                return
            msg = dashboard.append_patient_message(
                bed=bed, content=content, delivery_id=delivery_id
            )
            if msg is None:
                self._send_json(_err("留言失败"), 500)
                return
            review_result = None
            if _is_medication_review_message(content):
                review_result = _set_review_override_from_message(
                    dashboard, delivery_id, bed, content
                )
            try:
                dashboard.get_logger().info(
                    f"[patient_web] message bed={bed} delivery_id={delivery_id!r} "
                    f"content={content!r}"
                )
            except Exception:
                pass
            response_payload = {"message": msg}
            if review_result is not None:
                response_payload["review"] = review_result
            self._send_json(_ok(response_payload))

        # ----- 方法入口 -----
        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header(
                "Access-Control-Allow-Methods", "GET, POST, OPTIONS"
            )
            self.send_header(
                "Access-Control-Allow-Headers", "Content-Type, X-Patient-Token"
            )
            self.end_headers()

        def do_GET(self):
            try:
                parsed = urlparse(self.path)
                path = parsed.path
                params = parse_qs(parsed.query or "")
                if path == "/":
                    self._send_redirect(_BASE_PATH)
                    return
                if path == "/patient" or path == "/patient/":
                    self._serve_static(_BASE_PATH)
                    return
                # 新路径 (推荐)
                if path == "/patient/api/delivery":
                    self._api_delivery(params)
                    return
                if path == "/patient/api/identity":
                    self._api_identity(params)
                    return
                # 旧路径兼容
                if path == "/patient/api/order":
                    self._api_delivery(params)
                    return
                if path == "/patient/api/history":
                    self._api_history(params)
                    return
                if path == "/patient/api/messages":
                    self._api_messages_get(params)
                    return
                if path == "/patient/api/robot_status":
                    self._api_robot_status(params)
                    return
                if path.startswith("/patient/api/"):
                    self._send_json(_err("未知 API"), 404)
                    return
                if path.startswith(_BASE_PATH):
                    self._serve_static(path)
                    return
                self._send_text("Not found", 404)
            except Exception as exc:
                try:
                    dashboard.get_logger().error(
                        f"[patient_web] GET error: {exc}"
                    )
                    self._send_json(_err(str(exc)), 500)
                except Exception:
                    pass

        def do_POST(self):
            try:
                path = urlparse(self.path).path
                if not path.startswith(_API_PREFIX):
                    self._send_text("Not found", 404)
                    return
                body = self._read_body()
                # 新路径
                m = re.match(
                    r"^/patient/api/deliveries/([^/]+)/confirm$", path
                )
                if m:
                    self._api_confirm(unquote(m.group(1)), body)
                    return
                m = re.match(
                    r"^/patient/api/deliveries/([^/]+)/reject$", path
                )
                if m:
                    self._api_reject(unquote(m.group(1)), body)
                    return
                # 旧路径兼容
                m = re.match(r"^/patient/api/orders/([^/]+)/confirm$", path)
                if m:
                    self._api_confirm(unquote(m.group(1)), body)
                    return
                m = re.match(r"^/patient/api/orders/([^/]+)/reject$", path)
                if m:
                    self._api_reject(unquote(m.group(1)), body)
                    return
                if path == "/patient/api/call_robot":
                    self._api_call_robot(body)
                    return
                if path == "/patient/api/messages":
                    self._api_messages_post(body)
                    return
                if path == "/patient/api/voice/listen":
                    self._api_voice_listen(body)
                    return
                if path == "/patient/api/voice/announce":
                    self._api_voice_announce(body)
                    return
                self._send_json(_err("未知 API"), 404)
            except Exception as exc:
                try:
                    dashboard.get_logger().error(
                        f"[patient_web] POST error: {exc}"
                    )
                    self._send_json(_err(str(exc)), 500)
                except Exception:
                    pass

    return PatientHandler




