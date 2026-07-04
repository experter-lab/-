import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  CalendarDays,
  ChevronRight,
  Clock3,
  Hash,
  History,
  PackageCheck,
  PackageX,
  Pill,
} from "lucide-react"
import { STATUS_META } from "@/lib/status"
import type { DrugItem, PatientHistoryEntry } from "@/lib/types"

interface HistoryListProps {
  entries: PatientHistoryEntry[]
}

type Group = { label: string; items: PatientHistoryEntry[] }

type DetailIcon = typeof CalendarDays

function relativeDateLabel(datePart: string, now: Date): string {
  const m = String(now.getMonth() + 1).padStart(2, "0")
  const d = String(now.getDate()).padStart(2, "0")
  const today = `${m}/${d}`
  const yesterday = new Date(now.getTime() - 86400_000)
  const ymd = `${String(yesterday.getMonth() + 1).padStart(2, "0")}/${String(yesterday.getDate()).padStart(2, "0")}`
  if (datePart === today) return "\u4eca\u5929"
  if (datePart === ymd) return "\u6628\u5929"
  return datePart
}

function groupByDate(entries: PatientHistoryEntry[]): Group[] {
  const now = new Date()
  const map = new Map<string, PatientHistoryEntry[]>()
  for (const e of entries) {
    const datePart = e.date.split(" ")[0] || e.date
    const label = relativeDateLabel(datePart, now)
    const arr = map.get(label) ?? []
    arr.push(e)
    map.set(label, arr)
  }
  return Array.from(map.entries()).map(([label, items]) => ({ label, items }))
}

function compact(parts: Array<string | undefined | null | false>): string[] {
  return parts.map((item) => String(item || "").trim()).filter(Boolean)
}

function DrugHistoryCard({ drug }: { drug: DrugItem }) {
  const tags = compact([drug.route_label, drug.dose, drug.frequency, drug.timing])
  const detail = compact([drug.usage_text, drug.duration, drug.precautions, drug.doctor_note])
  return (
    <div className="min-w-0 rounded-2xl glass-card p-4">
      <div className="flex min-w-0 items-start gap-3">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
          <Pill className="h-5 w-5" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="break-words text-lg font-semibold leading-snug sm:text-xl">{drug.drug_name}</div>
          <div className="mt-1 text-base text-muted-foreground">
            {"\u6570\u91cf\uff1a"}{drug.quantity} {drug.unit ?? "\u4efd"}
          </div>
          {tags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-secondary px-3 py-1 text-sm font-medium text-secondary-foreground"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
          {detail.length > 0 && (
            <div className="mt-3 space-y-1 text-base leading-relaxed text-foreground/85">
              {detail.map((line) => (
                <div key={line}>{line}</div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function DetailRow({ icon: Icon, label, value }: {
  icon: DetailIcon
  label: string
  value: string
}) {
  return (
    <div className="flex items-start gap-3 rounded-2xl glass-card px-4 py-3">
      <Icon className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
      <div className="min-w-0">
        <div className="text-sm text-muted-foreground">{label}</div>
        <div className="mt-0.5 break-words text-lg font-semibold leading-snug">{value || "-"}</div>
      </div>
    </div>
  )
}

function HistoryDetailDialog({ entry, open, onOpenChange }: {
  entry: PatientHistoryEntry | null
  open: boolean
  onOpenChange: (v: boolean) => void
}) {
  if (!entry) return null
  const status = STATUS_META[entry.status]
  const StatusIcon = status.icon
  const drugs = entry.drugs ?? []

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[88svh] max-w-md overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex min-w-0 items-start gap-2.5 text-xl leading-snug sm:text-2xl">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary sm:h-11 sm:w-11">
              <PackageCheck className="h-6 w-6" />
            </span>
            {"\u5386\u53f2\u7528\u836f\u8be6\u60c5"}
          </DialogTitle>
          <DialogDescription className="text-base leading-relaxed">
            {"\u8fd9\u91cc\u663e\u793a\u8be5\u6b21\u9001\u836f\u7684\u65f6\u95f4\u3001\u72b6\u6001\u548c\u836f\u54c1\u660e\u7ec6\u3002"}
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto -mx-4 px-4 space-y-4 pb-1 sm:-mx-6 sm:px-6">
          <div className="grid gap-3">
            <DetailRow icon={CalendarDays} label="\u65f6\u95f4" value={entry.date} />
            <DetailRow icon={Hash} label="\u6279\u6b21" value={entry.delivery_id} />
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-2xl glass-card px-4 py-3">
              <div className="flex min-w-0 items-center gap-3">
                <StatusIcon className="h-5 w-5 text-primary" />
                <div>
                  <div className="text-sm text-muted-foreground">{"\u72b6\u6001"}</div>
                  <div className="mt-0.5 text-lg font-semibold">{status.text}</div>
                </div>
              </div>
              <Badge variant={status.badgeVariant} className="gap-1 text-sm">
                <StatusIcon className="h-3.5 w-3.5" />
                {status.text}
              </Badge>
            </div>
          </div>

          {drugs.length > 0 ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-lg font-semibold">
                <Pill className="h-5 w-5 text-primary" />
                {"\u836f\u54c1\u660e\u7ec6"} ({drugs.length})
              </div>
              {drugs.map((drug, index) => (
                <DrugHistoryCard key={`${drug.drug_id || drug.drug_name}-${index}`} drug={drug} />
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-950">
              <div className="text-lg font-bold">{"\u6682\u65e0\u5b8c\u6574\u836f\u54c1\u660e\u7ec6"}</div>
              <div className="mt-2 text-base leading-relaxed">
                {"\u8fd9\u6761\u5386\u53f2\u8bb0\u5f55\u76ee\u524d\u53ea\u6709\u7b7e\u6536\u6216\u914d\u9001\u6458\u8981\uff1a"}
                <span className="font-semibold">{entry.drugs_summary || "-"}</span>
                {"\u3002\u540e\u7eed\u5916\u90e8\u6279\u6b21\u63a5\u53e3\u8fd4\u56de\u660e\u7ec6\u540e\uff0c\u8fd9\u91cc\u4f1a\u81ea\u52a8\u663e\u793a\u836f\u54c1\u5217\u8868\u3002"}
              </div>
            </div>
          )}
        </div>

        <Button size="lg" onClick={() => onOpenChange(false)} className="min-h-14 h-auto text-base whitespace-normal sm:text-lg">
          {"\u77e5\u9053\u4e86"}
        </Button>
      </DialogContent>
    </Dialog>
  )
}

export function HistoryList({ entries }: HistoryListProps) {
  const [selected, setSelected] = useState<PatientHistoryEntry | null>(null)
  const groups = groupByDate(entries)

  return (
    <>
      <Card className="glass-panel">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-lg">
              <History className="h-5 w-5 text-primary" />
              {"\u6700\u8fd1\u7528\u836f"}
            </CardTitle>
            <span className="text-xs text-muted-foreground">{"\u6700\u8fd1 7 \u5929"}</span>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {entries.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-center gap-3">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted">
                <PackageX className="h-7 w-7 text-muted-foreground/70" />
              </div>
              <div className="text-base text-muted-foreground">
                {"\u6682\u65e0\u7528\u836f\u8bb0\u5f55"}
              </div>
            </div>
          ) : (
            <div className="space-y-5">
              {groups.map((g) => (
                <div key={g.label}>
                  <div className="flex items-center gap-2 mb-2.5">
                    <span className="rounded-full bg-secondary px-3 py-1 text-sm font-semibold text-secondary-foreground">
                      {g.label}
                    </span>
                    <div className="flex-1 h-px bg-border" />
                  </div>

                  <ol className="relative pl-6">
                    <div
                      aria-hidden
                      className="absolute left-2 top-2 bottom-2 w-px bg-border"
                    />
                    {g.items.map((e) => {
                      const s = STATUS_META[e.status]
                      const time = e.date.split(" ")[1] || ""
                      const StatusIcon = s.icon
                      return (
                        <li
                          key={e.delivery_id}
                          className="relative pb-3 last:pb-0"
                        >
                          <div
                            aria-hidden
                            className="absolute -left-[18px] top-4 flex h-3.5 w-3.5 items-center justify-center"
                          >
                            <div className="h-3 w-3 rounded-full bg-primary/15 ring-2 ring-card" />
                            <div className="absolute h-1.5 w-1.5 rounded-full bg-primary" />
                          </div>

                          <button
                            type="button"
                            onClick={() => setSelected(e)}
                            className="group flex w-full min-w-0 items-center justify-between gap-2 rounded-2xl bg-card/70 px-4 py-3 text-left shadow-sm transition-colors hover:bg-accent/60 focus:outline-none focus:ring-2 focus:ring-primary/35"
                            aria-label={`\u67e5\u770b${e.drugs_summary}\u7684\u5386\u53f2\u7528\u836f\u8be6\u60c5`}
                          >
                            <div className="min-w-0 flex-1">
                              <div className="text-lg font-semibold leading-snug truncate">
                                {e.drugs_summary || "\u7528\u836f\u8bb0\u5f55"}
                              </div>
                              <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-muted-foreground">
                                <span className="inline-flex items-center gap-1 font-mono">
                                  <Clock3 className="h-3.5 w-3.5" />
                                  {time || "--:--"}
                                </span>
                                <span className="min-w-0 break-all font-mono">{e.delivery_id}</span>
                              </div>
                            </div>
                            <div className="flex shrink-0 items-center gap-1.5">
                              <Badge
                                variant={s.badgeVariant}
                                className="gap-1 text-sm"
                              >
                                <StatusIcon className="h-3.5 w-3.5" />
                                {s.text}
                              </Badge>
                              <ChevronRight className="h-5 w-5 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
                            </div>
                          </button>
                        </li>
                      )
                    })}
                  </ol>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      <HistoryDetailDialog
        entry={selected}
        open={Boolean(selected)}
        onOpenChange={(open) => {
          if (!open) setSelected(null)
        }}
      />
    </>
  )
}
