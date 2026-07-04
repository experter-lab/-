interface RobotIllustrationProps {
  className?: string
  /** 是否带 bobbing 动画 (配送中) */
  animate?: boolean
}

/**
 * 简化机器人插画 SVG, 配送中状态显示
 * 矢量, 跟随 text 颜色 (默认 white over primary)
 */
export function RobotIllustration({
  className,
  animate,
}: RobotIllustrationProps) {
  return (
    <svg
      viewBox="0 0 96 96"
      className={`${className ?? ""} ${animate ? "animate-robot-bob" : ""}`}
      fill="none"
      role="img"
      aria-label="配送机器人"
    >
      {/* 阴影 */}
      <ellipse cx="48" cy="86" rx="22" ry="3" fill="currentColor" opacity="0.18" />
      {/* 底盘 */}
      <rect x="22" y="68" width="52" height="14" rx="4" fill="currentColor" opacity="0.55" />
      {/* 轮 */}
      <circle cx="32" cy="84" r="4" fill="currentColor" opacity="0.85" />
      <circle cx="64" cy="84" r="4" fill="currentColor" opacity="0.85" />
      {/* 身体 */}
      <rect x="26" y="32" width="44" height="38" rx="8" fill="currentColor" />
      {/* 药盒槽 */}
      <rect x="32" y="48" width="32" height="14" rx="2" fill="currentColor" opacity="0.25" />
      <path d="M40 52h16M40 56h16" stroke="currentColor" strokeWidth="1" opacity="0.45" />
      {/* 头 */}
      <rect x="32" y="14" width="32" height="22" rx="6" fill="currentColor" />
      {/* 眼 */}
      <circle cx="42" cy="25" r="2.5" fill="white" />
      <circle cx="54" cy="25" r="2.5" fill="white" />
      <circle cx="42.8" cy="25.5" r="1.1" fill="currentColor" />
      <circle cx="54.8" cy="25.5" r="1.1" fill="currentColor" />
      {/* 天线 */}
      <line x1="48" y1="14" x2="48" y2="8" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="48" cy="6.5" r="1.8" fill="currentColor" />
    </svg>
  )
}
