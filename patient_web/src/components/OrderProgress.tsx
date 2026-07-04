import { Check } from "lucide-react"
import { cn } from "@/lib/utils"
import { PROGRESS_STEPS, STATUS_META } from "@/lib/status"
import type { OrderStatus } from "@/lib/types"

interface OrderProgressProps {
  status: OrderStatus
}

/**
 * 4 步水平进度条: 备药 → 装载 → 配送 → 到达
 *
 * - 已完成步骤: 实心圆 + 勾选
 * - 当前步骤: 实心圆 + 自带柔脉冲 + 加粗 label
 * - 未来步骤: 空心圆 + 灰 label
 * - 拒收/取消: 标识到当前 step, 但加 ring-destructive
 */
export function OrderProgress({ status }: OrderProgressProps) {
  const meta = STATUS_META[status]
  const currentStep = meta.step
  const isError = status === "rejected" || status === "cancelled"

  return (
    <div className="relative min-w-0 overflow-hidden">
      {/* 背景细线 */}
      <div
        aria-hidden
        className="absolute left-5 right-5 top-5 h-[3px] rounded-full bg-border"
      />
      {/* 已走进度 */}
      <div
        aria-hidden
        className={cn(
          "absolute left-5 top-5 h-[3px] rounded-full transition-[width,background-color] duration-700 ease-out",
          isError ? "bg-destructive" : "bg-primary",
        )}
        style={{
          width: `calc((100% - 40px) * ${currentStep / (PROGRESS_STEPS.length - 1)})`,
        }}
      />

      <ol className="relative flex min-w-0 justify-between">
        {PROGRESS_STEPS.map((step, idx) => {
          const isDone = idx < currentStep || (idx === currentStep && meta.isFinal && !isError)
          const isCurrent = idx === currentStep && !meta.isFinal
          const isErrorHere = idx === currentStep && isError
          const Icon = step.icon

          return (
            <li
              key={step.key}
              className="flex min-w-0 flex-1 flex-col items-center gap-1.5"
            >
              <div
                className={cn(
                  "relative flex h-10 w-10 items-center justify-center rounded-full border-2 transition-[color,background-color,border-color,box-shadow] bg-card",
                  isDone &&
                    "border-primary bg-primary text-primary-foreground",
                  isCurrent &&
                    "border-primary bg-primary text-primary-foreground shadow-glow",
                  isErrorHere &&
                    "border-destructive bg-destructive text-destructive-foreground",
                  !isDone &&
                    !isCurrent &&
                    !isErrorHere &&
                    "border-border text-muted-foreground",
                )}
              >
                {/* 脉冲光环 - 仅当前步骤显示 */}
                {isCurrent && (
                  <span
                    aria-hidden
                    className="absolute inset-0 -m-0.5 rounded-full bg-primary/40 animate-pulse-ring"
                  />
                )}
                {isDone ? (
                  <Check className="h-5 w-5 relative" strokeWidth={3} />
                ) : (
                  <Icon className="h-5 w-5 relative" />
                )}
              </div>
              <div
                className={cn(
                  "max-w-[4.5rem] break-keep text-center text-[11px] leading-tight transition-colors sm:text-xs",
                  (isCurrent || isDone) && !isErrorHere
                    ? "font-semibold text-foreground"
                    : "text-muted-foreground",
                  isErrorHere && "font-semibold text-destructive",
                )}
              >
                {step.label}
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}
