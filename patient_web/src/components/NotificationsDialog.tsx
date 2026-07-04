import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { useNotifications } from "@/lib/NotificationsContext"
import type { NotificationItem, NotificationKind } from "@/lib/notifications"
import {
  Bell,
  CheckCheck,
  Info,
  Phone,
  Trash2,
  Truck,
  type LucideIcon,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface NotificationsDialogProps {
  open: boolean
  onOpenChange: (v: boolean) => void
}

const KIND_META: Record<
  NotificationKind,
  { icon: LucideIcon; tint: string; iconColor: string }
> = {
  order_status: {
    icon: Truck,
    tint: "bg-primary-soft text-primary",
    iconColor: "text-primary",
  },
  robot_call: {
    icon: Phone,
    tint: "bg-info-soft text-info-ink",
    iconColor: "text-info",
  },
  system: {
    icon: Info,
    tint: "bg-muted text-muted-foreground",
    iconColor: "text-muted-foreground",
  },
}

function relativeTime(iso: string): string {
  const t = new Date(iso).getTime()
  if (Number.isNaN(t)) return iso
  const diff = Date.now() - t
  if (diff < 60_000) return "刚刚"
  if (diff < 3600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86400_000) return `${Math.floor(diff / 3600_000)} 小时前`
  if (diff < 7 * 86400_000) return `${Math.floor(diff / 86400_000)} 天前`
  const d = new Date(t)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

export function NotificationsDialog({
  open,
  onOpenChange,
}: NotificationsDialogProps) {
  const { notifications, unreadCount, markRead, markAllRead, dismiss } =
    useNotifications()

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[82svh] max-w-md overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex min-w-0 flex-wrap items-center gap-2">
            <Bell className="h-5 w-5 text-primary" />
            通知中心
            {unreadCount > 0 && (
              <span className="ml-1 rounded-full bg-destructive px-2 py-0.5 text-xs font-bold text-destructive-foreground">
                {unreadCount} 条新
              </span>
            )}
          </DialogTitle>
          <DialogDescription>派送进度和系统消息会出现在这里</DialogDescription>
        </DialogHeader>

        {/* 工具行 */}
        <div className="-mt-2 flex min-w-0 flex-wrap items-center justify-between gap-2">
          <div className="text-xs text-muted-foreground">
            共 {notifications.length} 条
          </div>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={markAllRead}
              className="min-h-8 h-auto px-2 py-1 whitespace-normal"
            >
              <CheckCheck className="mr-1 h-4 w-4" />
              全部已读
            </Button>
          )}
        </div>

        {/* 列表 */}
        <div className="flex-1 overflow-y-auto -mx-4 px-4 space-y-2 sm:-mx-6 sm:px-6">
          {notifications.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">
              暂无通知
            </div>
          ) : (
            notifications.map((n) => (
              <NotificationRow
                key={n.id}
                item={n}
                onClick={() => !n.read && markRead(n.id)}
                onDismiss={() => dismiss(n.id)}
              />
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

function NotificationRow({
  item,
  onClick,
  onDismiss,
}: {
  item: NotificationItem
  onClick: () => void
  onDismiss: () => void
}) {
  const meta = KIND_META[item.kind]
  const Icon = meta.icon

  return (
    <div
      onClick={onClick}
      className={cn(
        "group relative rounded-xl border p-3 transition-colors cursor-pointer",
        item.read
          ? "border-border/70 bg-card/50"
          : "border-primary/30 bg-primary-soft/40 shadow-soft",
      )}
    >
      <div className="flex min-w-0 gap-3">
        <div
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-full",
            meta.tint,
          )}
        >
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <div
              className={cn(
                "min-w-0 break-words text-base",
                item.read ? "font-medium" : "font-semibold",
              )}
            >
              {item.title}
            </div>
            {!item.read && (
              <span
                aria-hidden
                className="h-2 w-2 shrink-0 rounded-full bg-destructive"
              />
            )}
          </div>
          <div className="mt-1 text-sm text-muted-foreground line-clamp-2">
            {item.body}
          </div>
          <div className="mt-1.5 text-xs text-muted-foreground/80">
            {relativeTime(item.createdAt)}
          </div>
        </div>
        <button
          type="button"
          aria-label="删除"
          onClick={(e) => {
            e.stopPropagation()
            onDismiss()
          }}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-muted-foreground/60 opacity-100 transition-opacity hover:bg-destructive/10 hover:text-destructive sm:opacity-0 sm:group-hover:opacity-100"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
