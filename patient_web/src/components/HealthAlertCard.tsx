import type { ReactNode } from "react"
import { AlertTriangle, HeartPulse, ShieldAlert, Stethoscope } from "lucide-react"
import type { PatientDelivery } from "@/lib/types"

interface HealthAlertCardProps {
  delivery: PatientDelivery | null
}

const TEXT = {
  title: "\u5065\u5eb7\u63d0\u9192",
  subtitle: "\u7528\u836f\u524d\u8bf7\u5148\u770b\u8fd9\u4e9b\u5173\u952e\u4fe1\u606f",
  diagnosis: "\u75be\u75c5\u8bca\u65ad",
  allergies: "\u8fc7\u654f\u53f2",
  contraindications: "\u7981\u5fcc / \u91cd\u70b9\u63d0\u9192",
  nursingNote: "\u62a4\u7406\u5907\u6ce8",
  empty: "\u6682\u672a\u5f55\u5165",
  safety: "\u8bf7\u4e0d\u8981\u81ea\u884c\u6539\u53d8\u5242\u91cf\u3001\u505c\u836f\u6216\u6362\u836f\u3002\u5982\u679c\u4fe1\u606f\u4e0d\u4e00\u81f4\uff0c\u5148\u8054\u7cfb\u62a4\u58eb\u6216\u533b\u751f\u3002",
}

function clean(value?: string) {
  return value?.trim() || ""
}

function InfoRow({
  icon,
  label,
  value,
  tone = "default",
}: {
  icon: ReactNode
  label: string
  value: string
  tone?: "default" | "warning"
}) {
  return (
    <div className={tone === "warning"
      ? "rounded-xl border border-amber-200/80 bg-amber-50/80 px-4 py-3"
      : "rounded-xl border border-emerald-100/80 bg-white/70 px-4 py-3"}
    >
      <div className={tone === "warning"
        ? "flex items-center gap-2 text-sm font-semibold text-amber-800"
        : "flex items-center gap-2 text-sm font-semibold text-slate-600"}
      >
        {icon}
        {label}
      </div>
      <div className="mt-1.5 text-lg font-semibold leading-relaxed text-slate-950">
        {value || TEXT.empty}
      </div>
    </div>
  )
}

export function HealthAlertCard({ delivery }: HealthAlertCardProps) {
  if (!delivery) return null

  const diagnosis = clean(delivery.diagnosis)
  const allergies = clean(delivery.allergies)
  const contraindications = clean(delivery.contraindications)
  const nursingNote = clean(delivery.nursing_note)

  if (!diagnosis && !allergies && !contraindications && !nursingNote) return null

  return (
    <section className="rounded-2xl border border-emerald-100/80 bg-white/82 p-4 shadow-sm backdrop-blur-xl">
      <div className="mb-3 flex items-start gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
          <HeartPulse className="h-6 w-6" />
        </div>
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-950">{TEXT.title}</h2>
          <p className="mt-1 text-base leading-relaxed text-slate-600">{TEXT.subtitle}</p>
        </div>
      </div>

      <div className="grid gap-2">
        <InfoRow
          icon={<Stethoscope className="h-4 w-4" />}
          label={TEXT.diagnosis}
          value={diagnosis}
        />
        <InfoRow
          icon={<ShieldAlert className="h-4 w-4" />}
          label={TEXT.allergies}
          value={allergies}
          tone={allergies && allergies !== "\u65e0" && !allergies.includes("\u65e0\u660e\u786e") ? "warning" : "default"}
        />
        <InfoRow
          icon={<AlertTriangle className="h-4 w-4" />}
          label={TEXT.contraindications}
          value={contraindications}
          tone="warning"
        />
        <InfoRow
          icon={<HeartPulse className="h-4 w-4" />}
          label={TEXT.nursingNote}
          value={nursingNote}
        />
      </div>

      <div className="mt-3 rounded-xl bg-slate-50 px-4 py-3 text-base leading-relaxed text-slate-700">
        {TEXT.safety}
      </div>
    </section>
  )
}
