import { useEffect, useMemo, useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import {
  AlertTriangle,
  CalendarClock,
  Clock,
  FlaskConical,
  Hash,
  Pill,
  Repeat,
  Square,
  Stethoscope,
  Volume2,
} from "lucide-react"
import type { LucideIcon } from "lucide-react"
import { announceVoice } from "@/lib/api"
import type { DrugItem } from "@/lib/types"

interface DrugDetailDialogProps {
  drug: DrugItem | null
  doctorName?: string
  doctorTitle?: string
  bed?: string
  deliveryId?: string
  open: boolean
  onOpenChange: (v: boolean) => void
}

function chineseNumberForSpeech(value: string | number, liangForTwo = false): string {
  const n = Number.parseInt(String(value), 10)
  if (!Number.isFinite(n)) return String(value)
  if (liangForTwo && n === 2) return "两"
  const digits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
  if (n < 0) return `负${chineseNumberForSpeech(-n, liangForTwo)}`
  if (n < 10) return digits[n]
  if (n < 20) return `十${n % 10 ? digits[n % 10] : ""}`
  if (n < 100) return `${digits[Math.floor(n / 10)]}十${n % 10 ? digits[n % 10] : ""}`
  if (n < 1000) {
    const h = Math.floor(n / 100)
    const r = n % 100
    if (r === 0) return `${digits[h]}百`
    if (r < 10) return `${digits[h]}百零${digits[r]}`
    return `${digits[h]}百${chineseNumberForSpeech(r, liangForTwo)}`
  }
  return String(n)
    .split("")
    .map((ch) => (/\d/.test(ch) ? digits[Number(ch)] : ch))
    .join(" ")
}

function normalizeSpeechText(text: string): string {
  const unitMap: Record<string, string> = {
    mg: "毫克",
    g: "克",
    ml: "毫升",
    l: "升",
    ug: "微克",
    μg: "微克",
    mcg: "微克",
    iu: "国际单位",
    mmhg: "毫米汞柱",
    "mmol/l": "毫摩尔每升",
  }
  let normalized = String(text || "")
  normalized = normalized.replace(/[０-９]/g, (ch) => String(ch.charCodeAt(0) - 0xff10)).replace(/\u3000/g, " ")
  normalized = normalized.replace(
    /(^|[^A-Za-z0-9])([0-9]+(?:\.[0-9]+)?)\s*(mmol\/l|mmHg|mcg|μg|ug|mg|ml|IU|iu|g|L|l)(?![A-Za-z])/gi,
    (_match, prefix: string, rawNum: string, rawUnit: string) => {
      const unit = rawUnit.toLowerCase()
      const spokenNum = rawNum.includes(".")
        ? rawNum.replace(/(\d+)\.(\d+)/, (_m, a, b) => `${chineseNumberForSpeech(a)}点${String(b).split("").map((ch) => chineseNumberForSpeech(ch)).join(" ")}`)
        : chineseNumberForSpeech(rawNum)
      return `${prefix}${spokenNum}${unitMap[unit] || rawUnit}`
    },
  )
  normalized = normalized.replace(/(\d+)\s*片/g, (_m, n) => `${chineseNumberForSpeech(n)}片`)
  normalized = normalized.replace(/(\d+)\s*粒/g, (_m, n) => `${chineseNumberForSpeech(n)}粒`)
  normalized = normalized.replace(/(\d+)\s*袋/g, (_m, n) => `${chineseNumberForSpeech(n)}袋`)
  normalized = normalized.replace(/(\d+)\s*盒/g, (_m, n) => `${chineseNumberForSpeech(n)}盒`)
  normalized = normalized.replace(/(\d+)\s*次/g, (_m, n) => `${chineseNumberForSpeech(n, true)}次`)
  normalized = normalized.replace(/每日\s*(\d+)/g, (_m, n) => `每日${chineseNumberForSpeech(n, true)}`)
  normalized = normalized.replace(/每天\s*(\d+)/g, (_m, n) => `每天${chineseNumberForSpeech(n, true)}`)
  normalized = normalized.replace(/一天\s*(\d+)/g, (_m, n) => `一天${chineseNumberForSpeech(n, true)}`)
  return normalized.replace(/\s+/g, " ").trim()
}
function normalizeUnitLabel(unit?: string): string {
  const raw = String(unit || "份").trim()
  // Some upstream prescriptions send unit as "1盒"/"1片" while quantity already stores the count.
  // Display/speech should be "5片", not "51片".
  return raw.replace(/^[1１]\s*(?=[盒片粒袋瓶支包板份])/u, "") || "份"
}

function formatQuantityText(quantity: string | number, unit?: string): string {
  return `${quantity}${normalizeUnitLabel(unit)}`
}
function compact(parts: Array<string | undefined | null | false>): string[] {
  return parts
    .map((item) => String(item || "").trim())
    .filter(Boolean)
}

function buildInstructionText(drug: DrugItem, doctorName?: string): string {
  const lines = compact([
    `\u836f\u54c1\uff1a${drug.drug_name}\u3002`,
    drug.route_label ? `\u7ed9\u836f\u65b9\u5f0f\uff1a${drug.route_label}\u3002` : undefined,
    drug.dose ? `\u5355\u6b21\u5242\u91cf\uff1a${drug.dose}\u3002` : undefined,
    drug.frequency ? `\u7528\u836f\u9891\u6b21\uff1a${drug.frequency}\u3002` : undefined,
    drug.timing ? `\u7528\u836f\u65f6\u95f4\uff1a${drug.timing}\u3002` : undefined,
    drug.duration ? `\u7597\u7a0b\uff1a${drug.duration}\u3002` : undefined,
    `\u672c\u6b21\u6570\u91cf\uff1a${formatQuantityText(drug.quantity, drug.unit)}\u3002`,
    drug.usage_text ? `\u7528\u836f\u8bf4\u660e\uff1a${drug.usage_text}\u3002` : undefined,
    drug.precautions ? `\u6ce8\u610f\u4e8b\u9879\uff1a${drug.precautions}\u3002` : undefined,
    drug.doctor_note ? `${doctorName || "\u533b\u751f"}\u5907\u6ce8\uff1a${drug.doctor_note}\u3002` : undefined,
  ])
  if (lines.length <= 2) {
    lines.push(
      "\u7cfb\u7edf\u6682\u672a\u6536\u5230\u8be5\u836f\u54c1\u7684\u8be6\u7ec6\u5242\u91cf\u548c\u9891\u6b21\uff0c\u8bf7\u6309\u533b\u751f\u6216\u62a4\u58eb\u5f53\u9762\u8bf4\u660e\u4f7f\u7528\u3002",
    )
  }
  lines.push(
    "\u4e0d\u8981\u81ea\u884c\u52a0\u91cf\u3001\u51cf\u91cf\u6216\u505c\u836f\u3002\u5982\u679c\u770b\u4e0d\u6e05\u6216\u6709\u7591\u95ee\uff0c\u8bf7\u547c\u53eb\u62a4\u58eb\u6838\u5bf9\u3002",
  )
  return lines.join("\n")
}

function speakInBrowser(text: string) {
  if (!("speechSynthesis" in window)) return false
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(normalizeSpeechText(text))
  utterance.lang = "zh-CN"
  utterance.rate = 0.85
  utterance.pitch = 1
  window.speechSynthesis.speak(utterance)
  return true
}

export function DrugDetailDialog({
  drug,
  doctorName,
  doctorTitle,
  bed,
  deliveryId,
  open,
  onOpenChange,
}: DrugDetailDialogProps) {
  const [speaking, setSpeaking] = useState(false)
  const [speakHint, setSpeakHint] = useState("")

  const instructionText = useMemo(
    () => (drug ? buildInstructionText(drug, doctorName) : ""),
    [drug, doctorName],
  )
  const speechInstructionText = useMemo(() => normalizeSpeechText(instructionText), [instructionText])

  useEffect(() => {
    if (!open && "speechSynthesis" in window) {
      window.speechSynthesis.cancel()
      setSpeaking(false)
    }
    return () => {
      if ("speechSynthesis" in window) window.speechSynthesis.cancel()
    }
  }, [open])

  if (!drug) return null

  const fields: Array<{
    icon: LucideIcon
    label: string
    value: string | undefined
  }> = [
    { icon: FlaskConical, label: "\u5355\u6b21\u5242\u91cf", value: drug.dose },
    { icon: Repeat, label: "\u7528\u836f\u9891\u6b21", value: drug.frequency },
    { icon: Pill, label: "\u7ed9\u836f\u65b9\u5f0f", value: drug.route_label },
    { icon: Clock, label: "\u7528\u836f\u65f6\u95f4", value: drug.timing },
    { icon: CalendarClock, label: "\u7597\u7a0b", value: drug.duration },
    { icon: Hash, label: "\u672c\u6b21\u6570\u91cf", value: formatQuantityText(drug.quantity, drug.unit) },
  ]
  const visibleFields = fields.filter((f) => !!f.value)
  const hasClinicalDetail = Boolean(
    drug.dose ||
      drug.frequency ||
      drug.route_label ||
      drug.timing ||
      drug.duration ||
      drug.usage_text ||
      drug.precautions ||
      drug.doctor_note,
  )

  async function handleSpeak() {
    if (!instructionText || speaking) return
    setSpeaking(true)
    const browserSpeaking = speakInBrowser(speechInstructionText)
    setSpeakHint(
      browserSpeaking
        ? "\u624b\u673a\u6b63\u5728\u64ad\u62a5\uff0c\u540c\u65f6\u6b63\u5728\u901a\u77e5\u8bbe\u5907\u2026"
        : "\u624b\u673a\u6d4f\u89c8\u5668\u4e0d\u652f\u6301\u672c\u673a\u64ad\u62a5\uff0c\u6b63\u5728\u901a\u77e5\u8bbe\u5907\u2026",
    )
    try {
      const result = await announceVoice({
        text: speechInstructionText,
        bed,
        delivery_id: deliveryId,
      })
      if (!result.ok) {
        setSpeakHint(
          browserSpeaking
            ? "\u624b\u673a\u6b63\u5728\u64ad\u62a5\uff0c\u8bbe\u5907\u64ad\u62a5\u672a\u8fde\u63a5"
            : result.error || "\u64ad\u62a5\u5931\u8d25\uff0c\u8bf7\u547c\u53eb\u62a4\u58eb",
        )
      } else {
        setSpeakHint(
          browserSpeaking
            ? "\u624b\u673a\u6b63\u5728\u64ad\u62a5\uff0c\u8bbe\u5907\u4e5f\u5df2\u63a5\u6536\u64ad\u62a5"
            : "\u5df2\u53d1\u9001\u5230\u8bbe\u5907\u8bed\u97f3\u64ad\u62a5",
        )
      }
    } catch (error) {
      setSpeakHint(
        browserSpeaking
          ? "\u624b\u673a\u6b63\u5728\u64ad\u62a5\uff0c\u8bbe\u5907\u64ad\u62a5\u672a\u8fde\u63a5"
          : error instanceof Error
            ? error.message
            : "\u64ad\u62a5\u5931\u8d25",
      )
    } finally {
      setTimeout(() => setSpeaking(false), 1200)
    }
  }

  function handleStopSpeak() {
    if ("speechSynthesis" in window) window.speechSynthesis.cancel()
    setSpeaking(false)
    setSpeakHint(
      "\u5df2\u505c\u6b62\u624b\u673a\u64ad\u62a5\u3002\u8bbe\u5907\u64ad\u62a5\u5982\u5df2\u5f00\u59cb\uff0c\u8bf7\u7b49\u5f85\u5f53\u524d\u53e5\u7ed3\u675f\u3002",
    )
  }
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[88svh] max-w-md overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex min-w-0 items-start gap-2.5 text-xl leading-snug sm:text-2xl">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary sm:h-11 sm:w-11">
              <Pill className="h-6 w-6" />
            </span>
            {drug.drug_name}
          </DialogTitle>
          <DialogDescription className="text-base leading-relaxed">
            {"\u8bf7\u5148\u6838\u5bf9\u836f\u540d\u3001\u6570\u91cf\u548c\u5305\u88c5\u3002\u70b9\u51fb\u64ad\u62a5\u540e\uff0c\u624b\u673a\u4f1a\u5c3d\u91cf\u76f4\u63a5\u64ad\u653e\uff0c\u8bbe\u5907\u4e5f\u4f1a\u540c\u6b65\u63a5\u6536\u64ad\u62a5\u3002"}
          </DialogDescription>
        </DialogHeader>

        <div className="grid min-w-0 gap-2 sm:grid-cols-2">
          <Button size="lg" onClick={handleSpeak} disabled={speaking} className="min-h-14 h-auto px-3 py-2 text-base whitespace-normal sm:text-lg">
            <Volume2 className="mr-2 h-5 w-5" />
            {speaking ? "\u64ad\u62a5\u4e2d" : "\u64ad\u62a5\u7528\u836f\u8bf4\u660e"}
          </Button>
          <Button size="lg" variant="outline" onClick={handleStopSpeak} className="min-h-14 h-auto px-3 py-2 text-base whitespace-normal sm:text-lg">
            <Square className="mr-2 h-5 w-5" />
            {"\u505c\u6b62\u64ad\u62a5"}
          </Button>
        </div>
        {speakHint && <div className="rounded-xl border border-primary/15 bg-primary-soft/50 px-3 py-2 text-sm font-medium leading-relaxed text-primary">{speakHint}</div>}

        <div className="flex-1 overflow-y-auto -mx-4 px-4 space-y-4 pb-1 sm:-mx-6 sm:px-6">
          {!hasClinicalDetail && (
            <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-950">
              <div className="flex items-start gap-2">
                <AlertTriangle className="mt-0.5 h-6 w-6 text-amber-600" />
                <div>
                  <div className="text-lg font-bold">{"\u6682\u65e0\u8be6\u7ec6\u533b\u5631"}</div>
                  <div className="mt-1 text-base leading-relaxed">
                    {"\u7cfb\u7edf\u672a\u6536\u5230\u8be5\u836f\u54c1\u7684\u5177\u4f53\u5242\u91cf\u3001\u9891\u6b21\u6216\u7597\u7a0b\u3002\u8bf7\u6309\u533b\u751f\u6216\u62a4\u58eb\u8bf4\u660e\u4f7f\u7528\uff0c\u4e0d\u8981\u81ea\u884c\u52a0\u51cf\u836f\u91cf\u3002"}
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="rounded-2xl border border-border/70 bg-card-sheen overflow-hidden">
            {visibleFields.map((f, idx) => (
              <div
                key={f.label}
                className={`flex items-start gap-3 px-4 py-3 ${
                  idx < visibleFields.length - 1 ? "border-b border-border/60" : ""
                }`}
              >
                <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <f.icon className="h-4.5 w-4.5" />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="text-sm text-muted-foreground">{f.label}</div>
                  <div className="mt-0.5 break-words text-lg font-semibold leading-snug sm:text-xl">{f.value}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-2xl bg-secondary/60 p-4 text-base leading-relaxed whitespace-pre-line sm:text-lg">
            {instructionText}
          </div>

          {drug.precautions && (
            <div className="rounded-2xl border border-warn/40 bg-warn-soft p-4">
              <div className="flex items-center gap-2 text-warn-ink">
                <AlertTriangle className="h-5 w-5" />
                <div className="text-lg font-semibold">{"\u6ce8\u610f\u4e8b\u9879"}</div>
              </div>
              <div className="mt-2 text-base text-warn-ink/90 leading-relaxed sm:text-lg">
                {drug.precautions}
              </div>
            </div>
          )}

          {drug.doctor_note && (
            <div className="rounded-2xl border border-primary/20 bg-primary-soft/60 p-4">
              <div className="flex items-center gap-2 text-primary">
                <Stethoscope className="h-5 w-5" />
                <div className="text-lg font-semibold">
                  {doctorName
                    ? `${doctorName} ${doctorTitle ?? ""} \u5907\u6ce8`
                    : "\u533b\u751f\u5907\u6ce8"}
                </div>
              </div>
              <div className="mt-2 text-base leading-relaxed sm:text-lg">{drug.doctor_note}</div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
