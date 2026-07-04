import { useEffect, useState } from "react"

/**
 * 当前时间, 默认每秒更新一次 (header 显示时分用)
 * 注意 strict mode 下 effect 会跑两次, 但 interval 是清理过的, 不会泄漏
 */
export function useNow(intervalMs = 1000): Date {
  const [now, setNow] = useState<Date>(() => new Date())
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), intervalMs)
    return () => clearInterval(t)
  }, [intervalMs])
  return now
}
