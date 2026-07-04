import { useEffect, useState } from "react"
import { BatteryFull, Bot, CheckCheck, Loader2, MapPin } from "lucide-react"
import { cn } from "@/lib/utils"
import { fetchRobotStatus } from "@/lib/api"
import type { RobotStatus } from "@/lib/types"

interface Props {
  bed: string
}

export function RobotStatusCard({ bed }: Props) {
  const [status, setStatus] = useState<RobotStatus | null>(null)

  useEffect(() => {
    if (!bed) return
    let cancelled = false
    const pull = async () => {
      try {
        const r = await fetchRobotStatus(bed)
        if (!cancelled && r.ok && r.data) setStatus(r.data)
      } catch {
        // 状态卡是辅助信息，拉取失败时不打断主流程。
      }
    }
    void pull()
    const t = setInterval(pull, 5000)
    return () => {
      cancelled = true
      clearInterval(t)
    }
  }, [bed])

  if (!status) {
    return (
      <div className="rounded-2xl border border-border/70 bg-card p-4 flex items-center gap-3 shadow-soft">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        <span className="text-base text-muted-foreground">正在获取机器人状态...</span>
      </div>
    )
  }

  const isMoving =
    status.stage === "on_the_way_to_me" ||
    status.stage === "on_the_way_other" ||
    status.stage === "loading" ||
    status.stage === "returning"
  const isForMe =
    status.for_me ||
    status.stage === "on_the_way_to_me" ||
    status.stage === "arrived_to_me"
  const isArrivedToMe = status.stage === "arrived_to_me"
  const isDone = status.stage === "done"

  const tone = isArrivedToMe
    ? "border-primary/70 bg-primary-soft"
    : isForMe
      ? "border-primary/50 bg-primary-soft/70"
      : isDone
        ? "border-border bg-muted/45"
        : "border-border bg-card"

  return (
    <div
      className={cn(
        "rounded-2xl glass-panel p-4 transition-colors",
        tone,
      )}
    >
      <div className="flex min-w-0 items-start gap-3">
        <div className="relative">
          {isMoving && (
            <span
              aria-hidden
              className="absolute -inset-1 rounded-full bg-primary/20 blur animate-soft-pulse"
            />
          )}
          <div
            className={cn(
              "relative flex h-12 w-12 items-center justify-center rounded-full",
              isForMe || isArrivedToMe
                ? "bg-primary text-primary-foreground"
                : isDone
                  ? "bg-muted text-muted-foreground"
                  : "bg-primary/12 text-primary",
            )}
          >
            {isArrivedToMe ? (
              <CheckCheck className="h-6 w-6" />
            ) : (
              <Bot className="h-6 w-6" />
            )}
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <div className="min-w-0 break-words text-lg font-semibold leading-snug tracking-tight">
              {status.human_text || "机器人状态正常"}
            </div>
            {isMoving && (
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
            )}
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
            <span className="inline-flex items-center gap-1">
              <MapPin className="h-4 w-4" />
              当前位置：{status.current_station_name || "未知"}
              {status.target_station_name &&
                status.target_station_name !== status.current_station_name && (
                  <span> → {status.target_station_name}</span>
                )}
            </span>
            {typeof status.battery === "number" && (
              <span className="inline-flex items-center gap-1">
                <BatteryFull className="h-4 w-4" />
                {Math.round(status.battery)}%
              </span>
            )}
            {!status.chassis_ok && (
              <span className="font-semibold text-destructive">底盘异常</span>
            )}
          </div>
        </div>
      </div>

      <ProgressLine stage={status.stage} />
    </div>
  )
}

const STAGES: { key: RobotStatus["stage"][]; label: string }[] = [
  { key: ["idle"], label: "待命" },
  { key: ["loading"], label: "装药" },
  { key: ["on_the_way_to_me", "on_the_way_other"], label: "配送中" },
  { key: ["arrived_to_me", "arrived_other"], label: "已到达" },
  { key: ["done", "returning"], label: "完成" },
]

function ProgressLine({ stage }: { stage: RobotStatus["stage"] }) {
  const currentIdx = STAGES.findIndex((s) => s.key.includes(stage))
  return (
    <div className="mt-4 grid min-w-0 grid-cols-5 gap-1">
      {STAGES.map((s, i) => {
        const active = currentIdx >= 0 && i <= currentIdx
        const current = i === currentIdx
        return (
          <div key={s.label} className="flex min-w-0 flex-col items-center">
            <div
              className={cn(
                "h-2 w-full rounded-full transition-colors",
                active ? "bg-primary" : "bg-border",
                current && "ring-2 ring-primary/25",
              )}
            />
            <span
              className={cn(
                "mt-1 max-w-full break-keep text-center text-[11px] leading-tight sm:text-xs",
                current
                  ? "text-primary font-semibold"
                  : active
                    ? "text-foreground/70"
                    : "text-muted-foreground/70",
              )}
            >
              {s.label}
            </span>
          </div>
        )
      })}
    </div>
  )
}
