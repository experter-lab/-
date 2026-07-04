import { useState } from "react"
import { AlertTriangle, CheckCircle2, Loader2, MessageSquareWarning } from "lucide-react"
import { Button } from "@/components/ui/button"
import { sendMessage } from "@/lib/api"
import type { PatientDelivery } from "@/lib/types"

interface ReportIssueCardProps {
  bed: string
  delivery: PatientDelivery | null
  onOpenMessage?: () => void
}

const TEXT = {
  title: "\u4fe1\u606f\u6709\u8bef\u6216\u770b\u4e0d\u61c2\uff1f",
  desc: "\u5982\u679c\u59d3\u540d\u3001\u8fc7\u654f\u53f2\u3001\u836f\u54c1\u6216\u5242\u91cf\u4e0d\u5bf9\uff0c\u8bf7\u5148\u901a\u77e5\u62a4\u58eb\uff0c\u4e0d\u8981\u81ea\u884c\u670d\u7528\u3002",
  send: "\u4fe1\u606f\u6709\u8bef\uff0c\u901a\u77e5\u62a4\u58eb",
  sending: "\u6b63\u5728\u901a\u77e5...",
  sent: "\u5df2\u901a\u77e5\u62a4\u58eb\uff0c\u8bf7\u7a0d\u7b49\u56de\u590d\u3002",
  failed: "\u53d1\u9001\u5931\u8d25\uff0c\u8bf7\u70b9\u51fb\u201c\u54a8\u8be2\u62a4\u58eb\u201d\u624b\u52a8\u7559\u8a00\u3002",
  openChat: "\u6253\u5f00\u54a8\u8be2",
}

function buildIssueMessage(delivery: PatientDelivery | null, bed: string) {
  const name = delivery?.patient_name || ""
  const ward = delivery?.ward || ""
  const drugs = (delivery?.drugs || [])
    .map((d) => d.drug_name)
    .filter(Boolean)
    .slice(0, 4)
    .join("\u3001")
  return [
    "\u3010\u75c5\u4eba\u7aef\u53cd\u9988\u3011\u6211\u89c9\u5f97\u5f53\u524d\u7528\u836f\u6216\u75c5\u4eba\u4fe1\u606f\u53ef\u80fd\u6709\u8bef\uff0c\u8bf7\u62a4\u58eb\u5e2e\u6211\u6838\u5bf9\u3002",
    `\u5e8a\u4f4d\uff1a${bed || "-"}`,
    ward ? `\u75c5\u533a\uff1a${ward}` : "",
    name ? `\u59d3\u540d\uff1a${name}` : "",
    drugs ? `\u5f53\u524d\u9875\u9762\u836f\u54c1\uff1a${drugs}` : "",
    "\u8bf7\u6838\u5bf9\u59d3\u540d\u3001\u8fc7\u654f\u53f2\u3001\u836f\u54c1\u540d\u79f0\u3001\u5242\u91cf\u548c\u670d\u7528\u65f6\u95f4\u3002",
  ].filter(Boolean).join("\n")
}

export function ReportIssueCard({ bed, delivery, onOpenMessage }: ReportIssueCardProps) {
  const [state, setState] = useState<"idle" | "sending" | "sent" | "failed">("idle")

  async function handleReport() {
    if (state === "sending") return
    setState("sending")
    const r = await sendMessage({
      bed,
      delivery_id: delivery?.delivery_id,
      content: buildIssueMessage(delivery, bed),
    })
    setState(r.ok ? "sent" : "failed")
  }

  const sent = state === "sent"
  const failed = state === "failed"

  return (
    <section className="rounded-2xl border border-amber-200/80 bg-amber-50/80 p-4 shadow-sm">
      <div className="flex min-w-0 gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-700">
          {sent ? <CheckCircle2 className="h-6 w-6" /> : <AlertTriangle className="h-6 w-6" />}
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="text-xl font-bold tracking-tight text-slate-950">{TEXT.title}</h2>
          <p className="mt-1 text-base leading-relaxed text-slate-700">{TEXT.desc}</p>
          <div className="mt-3 grid min-w-0 gap-2 sm:grid-cols-2">
            <Button
              type="button"
              variant={sent ? "outline" : "default"}
              className="min-h-12 h-auto rounded-xl px-3 py-2 text-base font-semibold whitespace-normal"
              onClick={handleReport}
              disabled={state === "sending" || sent}
            >
              {state === "sending" ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : <MessageSquareWarning className="mr-2 h-5 w-5" />}
              {state === "sending" ? TEXT.sending : sent ? TEXT.sent : TEXT.send}
            </Button>
            {onOpenMessage && (
              <Button
                type="button"
                variant="outline"
                className="min-h-12 h-auto rounded-xl bg-white/80 px-3 py-2 text-base font-semibold whitespace-normal"
                onClick={onOpenMessage}
              >
                {TEXT.openChat}
              </Button>
            )}
          </div>
          {failed && <div className="mt-2 text-sm font-medium text-destructive">{TEXT.failed}</div>}
        </div>
      </div>
    </section>
  )
}
