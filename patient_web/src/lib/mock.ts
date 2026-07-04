// 骨架阶段的 mock 数据, 让 UI 能立刻跑通
// 真实数据走 USE_MOCK=false + 后端 patient_http.py
import type { PatientDelivery, PatientHistoryEntry } from "./types"

export const MOCK_CURRENT_DELIVERY: PatientDelivery = {
  delivery_id: "PWB-302-20260611-001",
  bed: "302",
  patient_name: "张先生",
  status: "delivering",
  ward: "内科 3 楼",
  doctor_name: "李慧敏",
  doctor_title: "副主任医师",
  prescription_no: "RX-20260611-0301",
  prescription_note:
    "过敏史: 青霉素;近期监测肝肾功能,如出现皮疹或恶心立即告知护士。",
  dispatched_at: "2026-06-11T09:35:00+08:00",
  eta_seconds: 240,
  drugs: [
    {
      drug_id: "D001",
      drug_name: "阿莫西林胶囊",
      quantity: 1,
      unit: "盒",
      dose: "0.5 g",
      frequency: "每日 3 次",
      route: "oral",
      route_label: "口服",
      timing: "饭后服用",
      duration: "连服 5 天",
      precautions: "服药期间避免饮酒;如出现皮疹立即停药。",
      doctor_note: "对青霉素过敏者禁用",
    },
    {
      drug_id: "D002",
      drug_name: "布洛芬缓释胶囊",
      quantity: 1,
      unit: "盒",
      dose: "0.3 g",
      frequency: "每 12 小时 1 次",
      route: "oral",
      route_label: "口服",
      timing: "随餐",
      duration: "疼痛缓解后停药",
      precautions: "胃溃疡患者慎用;不与同类解热镇痛药合用。",
    },
    {
      drug_id: "D003",
      drug_name: "0.9% 氯化钠注射液",
      quantity: 2,
      unit: "袋",
      dose: "250 ml",
      frequency: "每日 1 次",
      route: "injection_iv",
      route_label: "静脉滴注",
      timing: "上午",
      duration: "3 天",
      precautions: "滴速控制 60 滴/分钟以下",
      doctor_note: "由护士操作",
    },
  ],
}

export const MOCK_HISTORY: PatientHistoryEntry[] = [
  {
    delivery_id: "PWB-302-20260610-002",
    date: "06/10 18:30",
    drugs_summary: "头孢克肟 ×2",
    status: "confirmed",
  },
  {
    delivery_id: "PWB-302-20260610-001",
    date: "06/10 09:15",
    drugs_summary: "维生素 C ×1",
    status: "confirmed",
  },
  {
    delivery_id: "PWB-302-20260609-002",
    date: "06/09 20:00",
    drugs_summary: "阿莫西林 ×2",
    status: "confirmed",
  },
  {
    delivery_id: "PWB-302-20260609-001",
    date: "06/09 09:00",
    drugs_summary: "降压药 ×1",
    status: "rejected",
  },
]
