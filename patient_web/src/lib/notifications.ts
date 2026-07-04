// 通知中心数据模型
// 当前 mock; 后端接入时改 fetch /patient/api/notifications
// 已读状态本地持久化, 即使后端不存也能用

export type NotificationKind =
  | "order_status"
  | "robot_call"
  | "system"

export interface NotificationItem {
  id: string
  kind: NotificationKind
  title: string
  body: string
  /** ISO 8601 */
  createdAt: string
  read: boolean
  orderId?: string
}

const STORAGE_KEY = "patient_web.notifications_read"

/** 读取已读 ID 集 */
export function loadReadSet(): Set<string> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return new Set()
    return new Set(JSON.parse(raw) as string[])
  } catch {
    return new Set()
  }
}

export function saveReadSet(s: Set<string>) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(s)))
  } catch {
    // ignore
  }
}

/** mock 通知数据 */
export const MOCK_NOTIFICATIONS: NotificationItem[] = [
  {
    id: "N-001",
    kind: "order_status",
    title: "药品派送中",
    body: "派送 PWB-302-20260611-001 已离开药房, 预计 5 分钟到达",
    createdAt: "2026-06-11T09:35:00+08:00",
    read: false,
    orderId: "PWB-302-20260611-001",
  },
  {
    id: "N-002",
    kind: "robot_call",
    title: "呼叫已受理",
    body: "护士台已收到您的呼叫, 工作人员正在处理",
    createdAt: "2026-06-11T08:20:00+08:00",
    read: false,
  },
  {
    id: "N-003",
    kind: "order_status",
    title: "派送已完成",
    body: "派送 PWB-302-20260610-002 已签收, 请按医嘱用药",
    createdAt: "2026-06-10T18:32:00+08:00",
    read: true,
    orderId: "PWB-302-20260610-002",
  },
  {
    id: "N-004",
    kind: "system",
    title: "欢迎使用取药终端",
    body: "本系统由医院信息科提供, 如有问题请联系护士台",
    createdAt: "2026-06-08T09:00:00+08:00",
    read: true,
  },
]
