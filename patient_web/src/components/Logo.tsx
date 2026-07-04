interface LogoProps {
  className?: string
  title?: string
}

/**
 * 医院方块 + 白十字 logo, 单色, 跟着 className 的 text 颜色走
 */
export function Logo({ className, title = "医院" }: LogoProps) {
  return (
    <svg
      viewBox="0 0 32 32"
      className={className}
      fill="none"
      aria-label={title}
      role="img"
    >
      <rect x="2" y="2" width="28" height="28" rx="8" fill="currentColor" />
      <path
        d="M13.5 8.5h5v5h5v5h-5v5h-5v-5h-5v-5h5v-5z"
        fill="white"
      />
    </svg>
  )
}
