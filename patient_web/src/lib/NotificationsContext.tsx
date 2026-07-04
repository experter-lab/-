import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import {
  loadReadSet,
  saveReadSet,
  MOCK_NOTIFICATIONS,
  type NotificationItem,
} from "@/lib/notifications"

interface NotificationsContextValue {
  notifications: NotificationItem[]
  unreadCount: number
  markRead: (id: string) => void
  markAllRead: () => void
  dismiss: (id: string) => void
  /** 后端真接入后, 这里改为 SSE 或 polling 拉新; 现在留接口 */
  push: (item: NotificationItem) => void
}

const NotificationsContext = createContext<NotificationsContextValue | null>(
  null,
)

export function NotificationsProvider({ children }: { children: ReactNode }) {
  // mock 阶段: 用 MOCK_NOTIFICATIONS 作为初始数据
  const [items, setItems] = useState<NotificationItem[]>(() => {
    const readSet = loadReadSet()
    return MOCK_NOTIFICATIONS.map((n) => ({
      ...n,
      read: n.read || readSet.has(n.id),
    }))
  })

  // 已读集持久化
  useEffect(() => {
    const readIds = new Set(items.filter((n) => n.read).map((n) => n.id))
    saveReadSet(readIds)
  }, [items])

  const markRead = useCallback((id: string) => {
    setItems((cur) =>
      cur.map((n) => (n.id === id ? { ...n, read: true } : n)),
    )
  }, [])

  const markAllRead = useCallback(() => {
    setItems((cur) => cur.map((n) => ({ ...n, read: true })))
  }, [])

  const dismiss = useCallback((id: string) => {
    setItems((cur) => cur.filter((n) => n.id !== id))
  }, [])

  const push = useCallback((item: NotificationItem) => {
    setItems((cur) => [item, ...cur])
  }, [])

  const unreadCount = useMemo(
    () => items.reduce((acc, n) => acc + (n.read ? 0 : 1), 0),
    [items],
  )

  const value = useMemo(
    () => ({
      notifications: items,
      unreadCount,
      markRead,
      markAllRead,
      dismiss,
      push,
    }),
    [items, unreadCount, markRead, markAllRead, dismiss, push],
  )

  return (
    <NotificationsContext.Provider value={value}>
      {children}
    </NotificationsContext.Provider>
  )
}

export function useNotifications(): NotificationsContextValue {
  const ctx = useContext(NotificationsContext)
  if (!ctx) {
    throw new Error(
      "useNotifications must be used within NotificationsProvider",
    )
  }
  return ctx
}
