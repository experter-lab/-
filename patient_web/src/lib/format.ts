export function greet(d: Date): string {
  const h = d.getHours()
  if (h < 6) return "夜深了"
  if (h < 9) return "早上好"
  if (h < 12) return "上午好"
  if (h < 14) return "中午好"
  if (h < 18) return "下午好"
  if (h < 22) return "晚上好"
  return "夜深了"
}

const WEEK = "日一二三四五六"

export function formatDate(d: Date): string {
  return `${d.getMonth() + 1}月${d.getDate()}日 周${WEEK[d.getDay()]}`
}

export function formatTime(d: Date): string {
  const hh = String(d.getHours()).padStart(2, "0")
  const mm = String(d.getMinutes()).padStart(2, "0")
  return `${hh}:${mm}`
}

export function formatDateShort(d: Date): string {
  return `${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getDate()).padStart(2, "0")}`
}

export function formatEta(secs?: number | null): string {
  if (secs === undefined || secs === null || secs <= 0) return ""
  if (secs < 60) return `约 ${Math.ceil(secs)} 秒`
  if (secs < 3600) return `约 ${Math.ceil(secs / 60)} 分钟`
  const h = Math.floor(secs / 3600)
  const m = Math.ceil((secs - h * 3600) / 60)
  return `约 ${h} 小时 ${m} 分钟`
}

export function formatEtaCompact(secs?: number | null): string {
  if (secs === undefined || secs === null || secs <= 0) return "--"
  if (secs < 60) return `${Math.ceil(secs)}s`
  if (secs < 3600) return `${Math.ceil(secs / 60)}m`
  return `${Math.floor(secs / 3600)}h${Math.ceil((secs % 3600) / 60)}m`
}

export function etaProgress(eta?: number | null, total = 600): number {
  if (eta === undefined || eta === null || eta <= 0) return 1
  const passed = Math.max(0, total - eta)
  return Math.min(1, Math.max(0, passed / total))
}
