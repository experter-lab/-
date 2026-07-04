import { Button } from "@/components/ui/button"
import { Logo } from "@/components/Logo"
import { Bell, LogOut, RefreshCw, Settings } from "lucide-react"

interface AppHeaderProps {
  subtitle?: string
  loading?: boolean
  unreadCount?: number
  onRefresh?: () => void
  onResetBed?: () => void
  onOpenNotifications?: () => void
  onOpenSettings?: () => void
}

/**
 * 顶部 sticky brand bar - logo + 终端名 + 工具栏
 * 病人侧统一外观, 所有页面共享
 */
export function AppHeader({
  subtitle = "取药终端",
  loading,
  unreadCount = 0,
  onRefresh,
  onResetBed,
  onOpenNotifications,
  onOpenSettings,
}: AppHeaderProps) {
  return (
    <header className="sticky top-0 z-30 surface-glass border-b border-border/70">
      <div className="app-shell flex h-14 min-w-0 items-center justify-between gap-1.5 px-3 sm:gap-2">
        <div className="flex min-w-0 items-center gap-2.5">
          <Logo className="h-8 w-8 text-primary drop-shadow-sm sm:h-9 sm:w-9" />
          <div className="min-w-0 truncate text-sm font-bold tracking-tight leading-none sm:text-[15px]">
            {subtitle}
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-0.5">
          {onOpenNotifications && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onOpenNotifications}
              aria-label="通知"
              className="relative h-9 w-9 sm:h-10 sm:w-10"
            >
              <Bell className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className="absolute top-2 right-2 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-bold text-destructive-foreground">
                  {unreadCount > 9 ? "9+" : unreadCount}
                </span>
              )}
            </Button>
          )}
          {onOpenSettings && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onOpenSettings}
              aria-label="设置"
              className="h-9 w-9 sm:h-10 sm:w-10"
            >
              <Settings className="h-5 w-5" />
            </Button>
          )}
          {onRefresh && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onRefresh}
              aria-label="刷新"
              className="h-9 w-9 sm:h-10 sm:w-10"
            >
              <RefreshCw
                className={`h-5 w-5 ${loading ? "animate-spin" : ""}`}
              />
            </Button>
          )}
          {onResetBed && (
            <Button
              variant="ghost"
              size="icon"
              onClick={onResetBed}
              aria-label="切换床位"
              className="h-9 w-9 sm:h-10 sm:w-10"
            >
              <LogOut className="h-5 w-5" />
            </Button>
          )}
        </div>
      </div>
    </header>
  )
}
