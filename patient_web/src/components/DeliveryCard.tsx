import { useEffect, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Hash,
  Loader2,
  MapPin,
  PackageX,
  Pill,
  ShieldAlert,
  Stethoscope,
  Truck,
  XCircle,
} from "lucide-react"
import { OrderProgress } from "@/components/OrderProgress"
import { EtaRing } from "@/components/EtaRing"
import { RobotIllustration } from "@/components/RobotIllustration"
import { DrugDetailDialog } from "@/components/DrugDetailDialog"
import { confirmDelivery, rejectDelivery } from "@/lib/api"
import { STATUS_META } from "@/lib/status"
import type { DrugItem, PatientDelivery } from "@/lib/types"

interface DeliveryCardProps {
  delivery: PatientDelivery
  onUpdated: () => void
}

const REJECT_REASONS = [
  "药品种类不对",
  "数量不对",
  "药品损坏 / 过期",
  "暂时不需要",
  "其他",
]

function formatDispatchedAt(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const m = String(d.getMonth() + 1).padStart(2, "0")
  const day = String(d.getDate()).padStart(2, "0")
  const hh = String(d.getHours()).padStart(2, "0")
  const mm = String(d.getMinutes()).padStart(2, "0")
  return `${m}/${day} ${hh}:${mm}`
}

function normalizeUnitLabel(unit?: string): string {
  const raw = String(unit || "份").trim()
  return raw.replace(/^[1１]\s*(?=[盒片粒袋瓶支包板份])/u, "") || "份"
}

function formatQuantityText(quantity: string | number, unit?: string): string {
  return `${quantity}${normalizeUnitLabel(unit)}`
}
/** 把一个药品的医嘱压成最多 3 个简短 chip 标签 */
function buildDrugChips(d: DrugItem): string[] {
  const out: string[] = []
  if (d.route_label) out.push(d.route_label)
  if (d.dose) out.push(d.dose)
  if (d.frequency) out.push(d.frequency)
  if (out.length < 3 && d.timing) out.push(d.timing)
  return out.slice(0, 3)
}

function DrugRow({
  drug,
  onOpenDetail,
}: {
  drug: DrugItem
  onOpenDetail: () => void
}) {
  const chips = buildDrugChips(drug)
  const hasDetail = true
  return (
    <button
      type="button"
      onClick={onOpenDetail}
      className="group block w-full min-w-0 rounded-2xl border border-border/70 glass-card p-4 text-left transition-[border-color,background-color,box-shadow] hover:border-primary/45 hover:bg-primary-soft/35 focus:outline-none focus:ring-2 focus:ring-primary/30"
      aria-label={
        hasDetail ? `查看 ${drug.drug_name} 的用药说明` : drug.drug_name
      }
    >
      <div className="flex min-w-0 items-start gap-3">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
          <Pill className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <div className="min-w-0 break-words text-lg font-semibold leading-snug">
              {drug.drug_name}
            </div>
            {drug.doctor_note && (
              <span
                title="包含医生备注"
                className="shrink-0 inline-flex h-4 w-4 items-center justify-center rounded-full bg-primary/15"
              >
                <Stethoscope className="h-2.5 w-2.5 text-primary" />
              </span>
            )}
          </div>
          {/* 医嘱 chips */}
          {chips.length > 0 ? (
            <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
              {chips.map((c, i) => (
                <span
                  key={`${c}-${i}`}
                  className={`inline-flex items-center rounded-full px-2.5 py-1 text-sm ${
                    i === 0
                      ? "bg-primary/10 text-primary font-medium"
                      : "bg-muted text-foreground/80"
                  }`}
                >
                  {c}
                </span>
              ))}
            </div>
          ) : (
            <div className="mt-1 text-sm text-muted-foreground">
              请按医生医嘱使用
            </div>
          )}
          {drug.precautions && (
            <div className="mt-2 flex items-start gap-1.5 text-sm text-warn-ink/90 line-clamp-1">
              <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
              <span className="truncate">{drug.precautions}</span>
            </div>
          )}
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <div className="text-xl font-bold leading-none text-primary sm:text-2xl">
            ×{formatQuantityText(drug.quantity, drug.unit)}
          </div>
          {hasDetail && (
            <ChevronRight className="mt-0.5 h-5 w-5 text-muted-foreground/70 transition-colors group-hover:text-primary" />
          )}
        </div>
      </div>
    </button>
  )
}

function StatusSpotlight({ delivery }: { delivery: PatientDelivery }) {
  const { status, eta_seconds } = delivery
  const reviewResolution = delivery.medication_review_resolution
  if (reviewResolution === "continue") {
    return (
      <div className="flex items-start gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-950">
        <CheckCircle2 className="mt-0.5 h-7 w-7 text-emerald-600" />
        <div>
          <div className="text-lg font-semibold">{"\u62a4\u58eb\u5df2\u590d\u6838\u901a\u8fc7\uff0c\u53ef\u4ee5\u7ee7\u7eed\u6838\u5bf9\u7b7e\u6536"}</div>
          <div className="mt-0.5 text-sm leading-relaxed opacity-85">
            {"\u533b\u62a4\u5df2\u6838\u5bf9\u672c\u6b21\u836f\u54c1\u4fe1\u606f\u3002\u8bf7\u60a8\u518d\u6b21\u786e\u8ba4\u59d3\u540d\u3001\u5e8a\u4f4d\u3001\u836f\u540d\u548c\u6570\u91cf\uff1b\u786e\u8ba4\u65e0\u8bef\u540e\u518d\u70b9\u51fb\u7b7e\u6536\uff0c\u4e0d\u786e\u5b9a\u65f6\u8bf7\u54a8\u8be2\u62a4\u58eb\u3002"}
          </div>
          {delivery.medication_review_resolved_at && (
            <div className="mt-2 text-xs opacity-75">复核时间：{delivery.medication_review_resolved_at}</div>
          )}
        </div>
      </div>
    )
  }
  if (reviewResolution === "return") {
    return (
      <div className="flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-red-950">
        <PackageX className="mt-0.5 h-7 w-7 text-red-600" />
        <div>
          <div className="text-lg font-semibold">药品已退回药房，请等待重新处理</div>
          <div className="mt-0.5 text-sm leading-relaxed opacity-85">
            护士已根据您的反馈暂停本次交付，药品会回到药房复核。请不要服用这批药，等待医护或药房重新通知。
          </div>
          {delivery.medication_review_resolution_reason && (
            <div className="mt-2 text-sm font-medium">原因：{delivery.medication_review_resolution_reason}</div>
          )}
        </div>
      </div>
    )
  }
  if (status === "delivering" || status === "dispatched") {
    return (
      <div className="flex items-center gap-4 rounded-2xl border border-primary/15 bg-primary-soft/60 p-4">
        <EtaRing etaSeconds={eta_seconds} />
        <div className="flex-1 min-w-0">
          <div className="text-base font-semibold text-foreground">
            药品正在送往您的床位
          </div>
          <div className="mt-1 text-sm text-muted-foreground">
            请保持手机畅通，到达时会提醒您
          </div>
        </div>
        <RobotIllustration
          className="h-16 w-16 text-primary hidden sm:block"
          animate
        />
      </div>
    )
  }
  if (status === "arrived") {
    return (
      <div className="relative overflow-hidden rounded-2xl bg-primary-sheen p-5 text-primary-foreground">
        <div
          aria-hidden
          className="absolute -right-4 -top-4 h-24 w-24 rounded-full bg-white/15"
        />
        <div className="relative flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-white/20">
            <MapPin className="h-7 w-7" />
          </div>
          <div>
            <div className="text-xl font-bold">机器人已到达床旁</div>
            <div className="mt-1 text-sm opacity-90">
              请核对药品，并点击下方“已收到”
            </div>
          </div>
        </div>
      </div>
    )
  }
  if (status === "timeout") {
    return (
      <div className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-950">
        <Clock3 className="mt-0.5 h-7 w-7 text-amber-600" />
        <div>
          <div className="text-lg font-semibold">等待您确认取药</div>
          <div className="mt-0.5 text-sm opacity-85">
            机器人已到位较久，医护端已收到提醒；您仍可核对后确认收药。
          </div>
        </div>
      </div>
    )
  }
  if (status === "review") {
    return (
      <div className="flex items-start gap-3 rounded-2xl border border-orange-200 bg-orange-50 p-4 text-orange-950">
        <AlertTriangle className="mt-0.5 h-7 w-7 text-orange-600" />
        <div>
          <div className="text-lg font-semibold">{"\u5df2\u901a\u77e5\u62a4\u58eb\u590d\u6838\uff0c\u8bf7\u5148\u4e0d\u8981\u670d\u7528"}</div>
          <div className="mt-0.5 text-sm leading-relaxed opacity-85">
            {"\u5de5\u4f5c\u53f0\u5df2\u6536\u5230\u60a8\u7684\u53cd\u9988\u3002\u533b\u62a4\u6b63\u5728\u6838\u5bf9\u59d3\u540d\u3001\u5e8a\u4f4d\u3001\u836f\u540d\u3001\u6570\u91cf\u548c\u5242\u91cf\uff1b\u590d\u6838\u5b8c\u6210\u524d\uff0c\u8bf7\u4fdd\u7559\u836f\u54c1\u539f\u5305\u88c5\uff0c\u4e0d\u8981\u6253\u5f00\u6216\u670d\u7528\u3002"}
          </div>
        </div>
      </div>
    )
  }
  if (status === "confirmed") {
    return (
      <div className="flex items-center gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-900">
        <CheckCircle2 className="h-7 w-7 text-emerald-600" />
        <div>
          <div className="text-lg font-semibold">已签收，请按医嘱用药</div>
          <div className="text-sm opacity-80 mt-0.5">
            如有用药疑问可咨询护士台
          </div>
        </div>
      </div>
    )
  }
  if (status === "rejected") {
    return (
      <div className="flex items-center gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-red-900">
        <XCircle className="h-7 w-7 text-red-600" />
        <div>
          <div className="text-lg font-semibold">{"\u60a8\u5df2\u53cd\u9988\u95ee\u9898\uff0c\u8bf7\u7b49\u5f85\u533b\u62a4\u5904\u7406"}</div>
          <div className="text-sm opacity-80 mt-0.5">
            {"\u5de5\u4f5c\u53f0\u5df2\u540c\u6b65\u663e\u793a\u5f02\u5e38\u3002\u5904\u7406\u5b8c\u6210\u524d\uff0c\u8bf7\u4e0d\u8981\u670d\u7528\u8fd9\u6279\u836f\u3002"}
          </div>
        </div>
      </div>
    )
  }
  if (status === "cancelled") {
    return (
      <div className="flex items-center gap-3 rounded-2xl border border-border bg-muted p-4 text-muted-foreground">
        <Loader2 className="h-6 w-6" />
        <div className="text-base">本次派送已取消</div>
      </div>
    )
  }
  // prescribed / preparing
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-border/70 bg-muted/60 p-4">
      <Loader2 className="h-6 w-6 text-primary animate-spin" />
      <div>
        <div className="text-base font-semibold">
          {STATUS_META[status].text}
        </div>
        <div className="mt-0.5 text-sm text-muted-foreground">
          {STATUS_META[status].description}
        </div>
      </div>
    </div>
  )
}

export function DeliveryCard({ delivery, onUpdated }: DeliveryCardProps) {
  const [submitting, setSubmitting] = useState(false)
  const [rejectOpen, setRejectOpen] = useState(false)
  const [rejectReason, setRejectReason] = useState<string>("")
  const [detailDrug, setDetailDrug] = useState<DrugItem | null>(null)
  const [identityConfirmed, setIdentityConfirmed] = useState(false)
  const [actionMessage, setActionMessage] = useState<string>("")
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [confirmChecklist, setConfirmChecklist] = useState(false)

  const meta = STATUS_META[delivery.status]
  const reviewReturned = delivery.medication_review_resolution === "return"
  const reviewContinued = delivery.medication_review_resolution === "continue"
  const canConfirm = !reviewReturned && (delivery.status === "arrived" || delivery.status === "timeout")
  const canReject = !reviewReturned && (delivery.status === "arrived" || delivery.status === "timeout")
  const identityRequired = !reviewReturned && !["confirmed", "rejected", "review", "cancelled"].includes(delivery.status)
  const Icon = meta.icon

  useEffect(() => {
    const key = `patient_web.identity_confirmed.${delivery.delivery_id}`
    setIdentityConfirmed(window.localStorage.getItem(key) === "1")
    setConfirmOpen(false)
    setConfirmChecklist(false)
  }, [delivery.delivery_id])

  function handleIdentityConfirm() {
    const key = `patient_web.identity_confirmed.${delivery.delivery_id}`
    window.localStorage.setItem(key, "1")
    setIdentityConfirmed(true)
  }

  async function handleIdentityReject() {
    setSubmitting(true)
    const r = await rejectDelivery(
      delivery.delivery_id,
      "不是本人或床位信息不匹配，请医护复核",
      delivery.bed,
    )
    setSubmitting(false)
    if (r.ok) onUpdated()
  }

  function openConfirmDialog() {
    if (identityRequired && !identityConfirmed) return
    setConfirmChecklist(false)
    setConfirmOpen(true)
  }

  async function handleConfirm() {
    if (identityRequired && !identityConfirmed) return
    if (!confirmChecklist) {
      setActionMessage("\u8bf7\u5148\u52fe\u9009\u5df2\u7ecf\u6838\u5bf9\u59d3\u540d\u3001\u5e8a\u4f4d\u3001\u836f\u540d\u548c\u6570\u91cf\uff0c\u518d\u5b8c\u6210\u7b7e\u6536\u3002")
      return
    }
    setActionMessage("\u6b63\u5728\u63d0\u4ea4\u672c\u4eba\u7b7e\u6536\uff0c\u8bf7\u7a0d\u5019\u3002")
    setSubmitting(true)
    const r = await confirmDelivery(delivery.delivery_id, delivery.bed)
    setSubmitting(false)
    if (r.ok) {
      setConfirmOpen(false)
      setConfirmChecklist(false)
      setActionMessage("\u5df2\u5b8c\u6210\u672c\u4eba\u7b7e\u6536\uff0c\u5de5\u4f5c\u53f0\u4f1a\u540c\u6b65\u663e\u793a\u672c\u6b21\u9001\u836f\u5df2\u7b7e\u6536\u3002")
      onUpdated()
    } else {
      setActionMessage(r.error || "\u7b7e\u6536\u63d0\u4ea4\u5931\u8d25\uff0c\u8bf7\u8054\u7cfb\u62a4\u58eb\u5904\u7406\u3002")
    }
  }

  async function handleReject() {
    if (!rejectReason) return
    setActionMessage("正在提交反馈，请稍候。")
    setSubmitting(true)
    const r = await rejectDelivery(
      delivery.delivery_id,
      rejectReason,
      delivery.bed,
    )
    setSubmitting(false)
    setRejectOpen(false)
    if (r.ok) {
      setActionMessage("已提交反馈，工作台会显示需要医护复核。")
      onUpdated()
    } else {
      setActionMessage(r.error || "反馈提交失败，请联系护士处理。")
    }
  }

  async function handlePatientAbsent() {
    setActionMessage("正在通知医护您暂时不在床旁。")
    setSubmitting(true)
    const r = await rejectDelivery(
      delivery.delivery_id,
      "我暂时不在床旁，请转医护复核",
      delivery.bed,
    )
    setSubmitting(false)
    if (r.ok) onUpdated()
  }

  return (
    <>
      <Card className="glass-panel animate-fade-in-up">
        <CardHeader className="pb-3">
          <div className="flex min-w-0 items-start justify-between gap-3">
            <div className="flex min-w-0 items-center gap-2 text-sm text-muted-foreground">
              <Truck className="h-4 w-4" />
              <span className="min-w-0 truncate font-mono text-xs">
                {delivery.delivery_id}
              </span>
            </div>
            <Badge
              variant={meta.badgeVariant}
              className="shrink-0 gap-1 px-3 py-1.5 text-sm"
            >
              <Icon className="h-3.5 w-3.5" />
              {meta.text}
            </Badge>
          </div>
          <div className="mt-2 text-xl font-bold tracking-tight">
            本次药品派送
          </div>
          <div className="min-w-0 break-words text-base text-muted-foreground">
            {delivery.doctor_name && (
              <>
                <span className="inline-flex min-w-0 items-center gap-1">
                  <Stethoscope className="h-3.5 w-3.5" />
                  {delivery.doctor_name}
                  {delivery.doctor_title && (
                    <span className="text-muted-foreground/80">
                      {" "}{delivery.doctor_title}
                    </span>
                  )}
                </span>
                <span className="mx-1.5">·</span>
              </>
            )}
            派送启动 {formatDispatchedAt(delivery.dispatched_at)}
            {delivery.prescription_no && (
              <>
                <span className="mx-1.5">·</span>
                <span className="inline-flex min-w-0 items-center gap-0.5 break-all font-mono text-sm">
                  <Hash className="h-3 w-3" />
                  {delivery.prescription_no}
                </span>
              </>
            )}
          </div>
        </CardHeader>

        <CardContent className="space-y-5">
          {/* 步骤进度 */}
          <OrderProgress status={delivery.status} />

          {/* 当前状态焦点 */}
          <StatusSpotlight delivery={delivery} />

          {reviewContinued && delivery.medication_review_resolution_reason && (
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-4 text-sm leading-relaxed text-emerald-950">
              复核说明：{delivery.medication_review_resolution_reason}
            </div>
          )}

          {identityRequired && !identityConfirmed ? (
            <div className="min-w-0 rounded-2xl border-2 border-primary/30 bg-primary-soft/60 p-4">
              <div className="flex min-w-0 items-start gap-3">
                <ShieldAlert className="mt-0.5 h-6 w-6 text-primary" />
                <div className="min-w-0 flex-1">
                  <div className="text-lg font-bold">请先确认身份</div>
                  <div className="mt-2 grid gap-2 text-base sm:grid-cols-3">
                    <div className="rounded-xl bg-background/80 px-3 py-2">
                      <div className="text-xs text-muted-foreground">姓名</div>
                      <div className="font-semibold">{delivery.patient_name || "当前患者"}</div>
                    </div>
                    <div className="rounded-xl bg-background/80 px-3 py-2">
                      <div className="text-xs text-muted-foreground">床号</div>
                      <div className="font-semibold">{delivery.bed}</div>
                    </div>
                    <div className="rounded-xl bg-background/80 px-3 py-2">
                      <div className="text-xs text-muted-foreground">病区</div>
                      <div className="font-semibold">{delivery.ward || "当前病区"}</div>
                    </div>
                  </div>
                  <div className="mt-3 text-sm leading-relaxed text-muted-foreground">
                    确认后才会显示药品明细和签收按钮。若信息不符，请选择“不是我”，系统会通知药房端和医护复核。
                  </div>
                  <div className="mt-4 grid min-w-0 gap-3 sm:grid-cols-2">
                    <Button
                      size="lg"
                      onClick={handleIdentityConfirm}
                      disabled={submitting}
                      className="min-h-14 h-auto px-3 py-2 whitespace-normal"
                    >
                      <CheckCircle2 className="mr-2 h-5 w-5" />
                      是我本人
                    </Button>
                    <Button
                      size="lg"
                      variant="outline"
                      onClick={handleIdentityReject}
                      disabled={submitting}
                      className="min-h-14 h-auto border-2 px-3 py-2 whitespace-normal"
                    >
                      <XCircle className="mr-2 h-5 w-5" />
                      不是我
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          {(delivery.status === "arrived" || delivery.status === "timeout") && (
            <div className="rounded-2xl border-2 border-amber-300 bg-amber-50 p-4 text-amber-950">
              <div className="flex items-start gap-2">
                <Clock3 className="mt-0.5 h-5 w-5 text-amber-600" />
                <div>
                  <div className="font-semibold">请完成本人签收</div>
                  <div className="mt-1 text-sm leading-relaxed">
                    核对姓名、床位和药品包装后点击“本人确认签收”。签收结果会同步到配送工作台，作为本次送药状态记录。
                  </div>
                </div>
              </div>
            </div>
          )}

          {actionMessage && (
            <div className="rounded-2xl border border-primary/20 bg-primary-soft/50 p-4 text-base font-medium text-primary">
              {actionMessage}
            </div>
          )}
          {/* 主治医嘱总览 */}
          {(!identityRequired || identityConfirmed) && delivery.prescription_note && (
            <div className="rounded-2xl border border-primary/20 bg-primary-soft/50 p-4">
              <div className="flex items-center gap-2 text-primary">
                <ShieldAlert className="h-5 w-5" />
                <div className="font-semibold">主治医嘱</div>
              </div>
              <div className="mt-2 text-base leading-relaxed">
                {delivery.prescription_note}
              </div>
            </div>
          )}

          {/* 药品列表 */}
          {(!identityRequired || identityConfirmed) && (
          <div className="space-y-2">
            <div className="flex min-w-0 items-center justify-between">
              <div className="flex min-w-0 flex-wrap items-center gap-1.5 text-sm font-medium text-muted-foreground">
                <Pill className="h-3.5 w-3.5" />
                {"\u672c\u6b21\u836f\u54c1"} ({delivery.drugs.length}) {"\u00b7 \u70b9\u5f00\u53ef\u770b\u5927\u5b57\u8bf4\u660e\u548c\u8bed\u97f3\u64ad\u62a5"}
              </div>
            </div>
            <div className="space-y-2">
              {delivery.drugs.map((d) => (
                <DrugRow
                  key={d.drug_id}
                  drug={d}
                  onOpenDetail={() => setDetailDrug(d)}
                />
              ))}
            </div>
          </div>
          )}

          {/* 操作按钮 - 仅到达时显示 */}
          {(canConfirm || canReject) && (!identityRequired || identityConfirmed) && (
            <div className="grid min-w-0 gap-3 pt-1 sm:grid-cols-3">
              <Button
                size="lg"
                onClick={openConfirmDialog}
                disabled={submitting || !canConfirm}
                className="min-h-16 h-auto px-3 py-3 text-base shadow-glow whitespace-normal sm:px-4 sm:text-xl"
              >
                {submitting ? (
                  <Loader2 className="mr-2 h-6 w-6 animate-spin" />
                ) : (
                  <CheckCircle2 className="mr-2 h-6 w-6" />
                )}
                本人确认签收
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={handlePatientAbsent}
                disabled={submitting || !canReject}
                className="min-h-16 h-auto border-2 px-3 py-3 text-base whitespace-normal sm:text-xl"
              >
                <MapPin className="mr-2 h-6 w-6" />
                我暂时不在床旁
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={() => setRejectOpen(true)}
                disabled={submitting || !canReject}
                className="min-h-16 h-auto border-2 px-3 py-3 text-base whitespace-normal sm:text-xl"
              >
                <AlertTriangle className="mr-2 h-6 w-6" />
                药品有疑问
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={confirmOpen} onOpenChange={(open) => {
        setConfirmOpen(open)
        if (!open) setConfirmChecklist(false)
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{"\u6700\u540e\u786e\u8ba4\u540e\u518d\u7b7e\u6536"}</DialogTitle>
            <DialogDescription>
              {"\u8bf7\u6162\u6162\u6838\u5bf9\u3002\u53ea\u6709\u786e\u8ba4\u65e0\u8bef\u540e\uff0c\u624d\u70b9\u51fb\u4e0b\u65b9\u7eff\u8272\u6309\u94ae\u5b8c\u6210\u7b7e\u6536\u3002"}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="rounded-2xl border border-border/70 bg-muted/50 p-4 text-base leading-relaxed">
              <div className="font-semibold text-foreground">{"\u9700\u8981\u6838\u5bf9\u7684\u4fe1\u606f"}</div>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground">
                <li>{"\u59d3\u540d\uff1a"}{delivery.patient_name || "\u5f53\u524d\u60a3\u8005"}</li>
                <li>{"\u5e8a\u53f7\uff1a"}{delivery.bed}</li>
                <li>{"\u836f\u54c1\u6570\u91cf\uff1a"}{delivery.drugs.length}{" \u79cd"}</li>
              </ul>
            </div>
            <div className="max-h-44 overflow-auto rounded-2xl border border-border/70 bg-background p-3">
              {delivery.drugs.map((drug) => (
                <div key={drug.drug_id} className="flex items-start justify-between gap-3 border-b border-border/60 py-2 last:border-b-0">
                  <div className="min-w-0 break-words font-semibold">{drug.drug_name}</div>
                  <div className="shrink-0 font-bold text-primary">?{formatQuantityText(drug.quantity, drug.unit)}</div>
                </div>
              ))}
            </div>
            <label className="flex cursor-pointer items-start gap-3 rounded-2xl border-2 border-primary/25 bg-primary-soft/50 p-4 text-base font-semibold leading-relaxed">
              <input
                type="checkbox"
                checked={confirmChecklist}
                onChange={(event) => setConfirmChecklist(event.target.checked)}
                className="mt-1 h-5 w-5 shrink-0 accent-primary"
              />
              <span>{"\u6211\u5df2\u7ecf\u6838\u5bf9\u59d3\u540d\u3001\u5e8a\u4f4d\u3001\u836f\u540d\u548c\u6570\u91cf\uff0c\u786e\u8ba4\u662f\u672c\u4eba\u7684\u836f\u3002"}</span>
            </label>
          </div>
          <DialogFooter className="gap-2 sm:gap-2">
            <Button variant="ghost" onClick={() => setConfirmOpen(false)} disabled={submitting}>
              {"\u8fd4\u56de\u518d\u770b\u770b"}
            </Button>
            <Button
              onClick={handleConfirm}
              disabled={!confirmChecklist || submitting || !canConfirm}
              className="min-h-14 h-auto px-4 py-2 text-base whitespace-normal sm:text-lg"
            >
              {submitting ? (
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              ) : (
                <CheckCircle2 className="mr-2 h-5 w-5" />
              )}
              {"\u8fd4\u56de\u518d\u770b\u770b"}??
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={rejectOpen} onOpenChange={setRejectOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>请告诉我们哪里有问题</DialogTitle>
            <DialogDescription>
              选择一个原因，我们会通知工作人员处理
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            {REJECT_REASONS.map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setRejectReason(r)}
                className={`w-full rounded-xl border-2 px-4 py-3 text-left text-lg transition-colors ${
                  rejectReason === r
                    ? "border-primary bg-primary/10"
                    : "border-border hover:bg-accent"
                }`}
              >
                {r}
              </button>
            ))}
          </div>
          <DialogFooter className="gap-2 sm:gap-2">
            <Button variant="ghost" onClick={() => setRejectOpen(false)}>
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={handleReject}
              disabled={!rejectReason || submitting}
            >
              提交反馈
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <DrugDetailDialog
        drug={detailDrug}
        doctorName={delivery.doctor_name}
        doctorTitle={delivery.doctor_title}
        bed={delivery.bed}
        deliveryId={delivery.delivery_id}
        open={detailDrug !== null}
        onOpenChange={(v) => !v && setDetailDrug(null)}
      />
    </>
  )
}
