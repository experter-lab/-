import { formatEtaCompact } from "@/lib/format"

interface EtaRingProps {
  etaSeconds?: number | null
  /** 全程预估时长 (秒), 用于算环进度。后端真给了 created_at + eta 可以更精确, mock 阶段固定 */
  totalSeconds?: number
  size?: number
  stroke?: number
  /** 中央 label 文案, 默认 "预计到达" */
  label?: string
}

/**
 * 配送中圆环进度: 中央显示剩余时间, 周围环填充 (已走/全程)
 */
export function EtaRing({
  etaSeconds,
  totalSeconds = 600,
  size = 132,
  stroke = 10,
  label = "预计到达",
}: EtaRingProps) {
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const safeEta = Math.max(0, etaSeconds ?? 0)
  const progress = Math.min(
    1,
    Math.max(0, (totalSeconds - safeEta) / totalSeconds),
  )

  return (
    <div
      className="relative shrink-0"
      style={{ width: size, height: size }}
      role="img"
      aria-label={`${label} ${formatEtaCompact(etaSeconds)}`}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="-rotate-90 drop-shadow-sm"
      >
        {/* 背景环 */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke="hsl(var(--muted))"
          strokeWidth={stroke}
          fill="none"
        />
        {/* 进度环 */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke="hsl(var(--primary))"
          strokeWidth={stroke}
          fill="none"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - progress)}
          strokeLinecap="round"
          className="transition-[stroke-dashoffset] duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <div className="text-3xl font-bold text-primary leading-none">
          {formatEtaCompact(etaSeconds)}
        </div>
        <div className="mt-1 text-[11px] text-muted-foreground uppercase tracking-wide">
          {label}
        </div>
      </div>
    </div>
  )
}
