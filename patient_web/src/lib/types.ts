// 病人侧 API 数据契约 - 与后端 patient_http.py 对齐
// 业务语境: 院内药品派送 (不是病人下单), 状态从医生医嘱/护士配药 → 机器人配送 → 病人核对取药

// 派送状态: 院内流转视角
export type DeliveryStatus =
  | "prescribed"   // 医生已开方, 等待药房处理
  | "preparing"    // 药房备药 / 装载中
  | "dispatched"   // 机器人已出发
  | "delivering"   // 配送中(在路上)
  | "arrived"      // 已到达床旁
  | "confirmed"    // 病人已核对取药
  | "rejected"     // 病人反馈问题
  | "review"       // 病人反馈异常, 等待护士复核
  | "cancelled"    // 已取消(医嘱变更等)
  | "timeout"      // 机器人已到位较久, 病人尚未确认, 系统已记录待处理提醒

// 给药途径
export type AdminRoute =
  | "oral"          // 口服
  | "injection_iv"  // 静脉注射
  | "injection_im"  // 肌肉注射
  | "topical"       // 外用
  | "inhalation"    // 吸入
  | "sublingual"    // 舌下
  | "other"

export interface DrugItem {
  drug_id: string
  drug_name: string
  /** 本次配送的份数 (盒/瓶/支) */
  quantity: number
  /** 份数单位, 默认 "盒" */
  unit?: string

  // 用药说明 (医嘱字段, 可选, 后端按需返回)
  dose?: string              // 单次剂量: "5mg" / "1片" / "10ml"
  frequency?: string         // 频次: "每日3次" / "每12小时" / "PRN"
  route?: AdminRoute         // 给药途径
  route_label?: string       // 路径中文显示, 后端拍平好的, 前端可直接用
  timing?: string            // 用法时机: "饭前" / "饭后" / "睡前" / "随餐"
  duration?: string          // 疗程: "连服3天" / "至症状缓解"
  precautions?: string       // 注意事项: "服药期间避免饮酒"
  doctor_note?: string       // 该药品的医生备注
  /** 该药品对应的口服 / 外用 等的总说明文本, 如果上面字段都没拆分, 这里给一段连续文字 */
  usage_text?: string
}

export interface PatientDelivery {
  /** 派送 ID (PWB-{bed}-{date} 或后端真实 task_id) */
  delivery_id: string
  bed: string
  patient_name?: string
  /** ???????? HIS ?? */
  age?: number | string
  /** ?????/?/?? */
  gender?: string
  /** ?? cm */
  height_cm?: number | string
  /** ?? kg */
  weight_kg?: number | string
  /** ???? / ???? */
  diagnosis?: string
  /** ??? */
  allergies?: string
  /** ?? / ???? */
  contraindications?: string
  /** ???? */
  nursing_note?: string
  /** Medication review state returned by nurse workflow. */
  medication_review_resolution?: "continue" | "return" | string
  medication_review_resolved_at?: string
  medication_review_resolution_reason?: string
  medication_review_reason?: string
  status: DeliveryStatus
  drugs: DrugItem[]
  /** 派送启动时间 (药房分发出去的时刻) */
  dispatched_at: string  // ISO 8601
  /** 配送中剩余秒数, status=delivering 时给 */
  eta_seconds?: number
  /** arrived 时刻 */
  delivered_at?: string
  confirmed_at?: string
  rejected_reason?: string
  /** 主治医生姓名 */
  doctor_name?: string
  /** 主治医生职称 */
  doctor_title?: string
  /** 整体医嘱备注 (跨药品的提醒, 如"过敏史: 青霉素") */
  prescription_note?: string
  /** 处方/医嘱编号 */
  prescription_no?: string
  /** 科室病房 */
  ward?: string
}

export interface PatientIdentity {
  bed: string
  ward: string
  patient_name: string
  age?: number | string
  gender?: string
  height_cm?: number | string
  weight_kg?: number | string
  diagnosis?: string
  allergies?: string
  contraindications?: string
  nursing_note?: string
  has_delivery: boolean
  delivery_id: string
}

export interface PatientHistoryEntry {
  /** 派送 ID */
  delivery_id: string
  date: string         // "06/09 18:30"
  drugs_summary: string  // "头孢克肟 ×2"
  status: DeliveryStatus
  /** 历史批次药品明细；旧签收日志可能只有摘要，没有完整明细 */
  drugs?: DrugItem[]
}

export interface CallRobotRequest {
  bed: string
  reason?: string
}

export interface PatientMessage {
  id: string
  bed: string
  /** 谁发的: 病人 / 护士 / 系统 (系统消息=自动事件回执, 如"病人已确认收药") */
  sender: "patient" | "nurse" | "system"
  /** 护士回复时的姓名/称呼; sender=patient/system 时为空串 */
  nurse_name?: string
  content: string
  /** 关联的派送 ID, 留空表示与具体派送无关 */
  delivery_id?: string
  /** 后端返回的 unix 时间戳 (秒) */
  created_at: number
  /** 病人是否已读此消息 (对护士回复有意义) */
  read_by_patient: boolean
  /** 护士是否已读此消息 (对病人提问有意义) */
  read_by_nurse: boolean
}

export interface SendMessageRequest {
  bed: string
  content: string
  delivery_id?: string
}

export interface RobotStatus {
  bed: string
  task_id: string
  task_state: string
  task_bed: string
  current_station: string
  current_station_name: string
  target_station: string
  target_station_name: string
  for_me: boolean
  stage:
    | "idle"
    | "loading"
    | "on_the_way_to_me"
    | "on_the_way_other"
    | "arrived_to_me"
    | "arrived_other"
    | "returning"
    | "done"
  human_text: string
  chassis_ok: boolean
  battery?: number
  stamp: number
}

export interface ApiResult<T = unknown> {
  ok: boolean
  data?: T
  error?: string
}

// 兼容 alias - 老组件改完后这里可以删
export type OrderStatus = DeliveryStatus
export type PatientOrder = PatientDelivery
