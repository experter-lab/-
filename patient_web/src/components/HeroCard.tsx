import { useNow } from "@/lib/useNow"
import { formatDate, formatTime, greet } from "@/lib/format"
import { BedDouble, Hospital, Ruler, Scale, ShieldCheck, UserRound } from "lucide-react"

interface HeroCardProps {
  bed: string
  wardName?: string
  patientName?: string
  age?: number | string
  gender?: string
  heightCm?: number | string
  weightKg?: number | string
}

const TEXT = {
  unknown: "\u672a\u5f55\u5165",
  currentWard: "\u5f53\u524d\u75c5\u623f",
  currentPatient: "\u5f53\u524d\u60a3\u8005",
  ward: "\u75c5\u533a",
  bed: "\u5e8a\u53f7",
  name: "\u59d3\u540d",
  age: "\u5e74\u9f84",
  gender: "\u6027\u522b",
  height: "\u8eab\u9ad8",
  weight: "\u4f53\u91cd",
  checkPrefix: "\u8bf7\u5148\u6838\u5bf9\uff1a",
  bedSuffix: "\u5e8a",
  mismatch: "\u5982\u4fe1\u606f\u4e0d\u4e00\u81f4\uff0c\u8bf7\u5148\u8054\u7cfb\u62a4\u58eb\u3002",
}

function formatValue(value: number | string | undefined, unit = "") {
  if (value === undefined || value === null || value === "") return TEXT.unknown
  return `${value}${unit}`
}

export function HeroCard({
  bed,
  wardName,
  patientName,
  age,
  gender,
  heightCm,
  weightKg,
}: HeroCardProps) {
  const now = useNow(30_000)
  const ward = wardName?.trim() || TEXT.currentWard
  const name = patientName?.trim() || TEXT.currentPatient

  return (
    <section className="app-shell px-3 pt-4 pb-2">
      <div className="relative overflow-hidden rounded-2xl glass-primary text-primary-foreground">
        <div aria-hidden className="absolute inset-x-0 top-0 h-px bg-white/30" />
        <div className="relative px-4 py-5 sm:px-5">
          <div className="flex min-w-0 items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="truncate text-base opacity-90">
                {greet(now)}{patientName ? `\uff0c${name}` : ""}
              </div>
              <div className="mt-2 flex min-w-0 flex-wrap items-baseline gap-x-3 gap-y-1">
                <div className="text-3xl font-bold tracking-tight">{formatTime(now)}</div>
                <div className="text-sm opacity-90">{formatDate(now)}</div>
              </div>
            </div>
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-white/16">
              <ShieldCheck className="h-6 w-6" />
            </div>
          </div>

          <div className="mt-5 grid gap-2">
            <div className="grid grid-cols-1 gap-2 min-[430px]:grid-cols-3">
              <div className="min-w-0 rounded-xl bg-white/14 px-3 py-2">
                <div className="flex items-center gap-1.5 text-sm opacity-85">
                  <Hospital className="h-4 w-4" />
                  {TEXT.ward}
                </div>
                <div className="mt-1 truncate text-lg font-bold">{ward}</div>
              </div>
              <div className="min-w-0 rounded-xl bg-white/14 px-3 py-2">
                <div className="flex items-center gap-1.5 text-sm opacity-85">
                  <BedDouble className="h-4 w-4" />
                  {TEXT.bed}
                </div>
                <div className="mt-1 truncate text-lg font-bold tracking-wide">{bed}</div>
              </div>
              <div className="min-w-0 rounded-xl bg-white/14 px-3 py-2">
                <div className="flex items-center gap-1.5 text-sm opacity-85">
                  <UserRound className="h-4 w-4" />
                  {TEXT.name}
                </div>
                <div className="mt-1 truncate text-lg font-bold">{name}</div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-2 min-[390px]:grid-cols-2 sm:grid-cols-4">
              <div className="min-w-0 rounded-xl border border-white/18 bg-white/12 px-3 py-2">
                <div className="text-xs opacity-80">{TEXT.age}</div>
                <div className="mt-0.5 break-words text-base font-semibold">{formatValue(age, age ? "\u5c81" : "")}</div>
              </div>
              <div className="min-w-0 rounded-xl border border-white/18 bg-white/12 px-3 py-2">
                <div className="text-xs opacity-80">{TEXT.gender}</div>
                <div className="mt-0.5 break-words text-base font-semibold">{gender?.trim() || TEXT.unknown}</div>
              </div>
              <div className="min-w-0 rounded-xl border border-white/18 bg-white/12 px-3 py-2">
                <div className="flex items-center gap-1 text-xs opacity-80">
                  <Ruler className="h-3.5 w-3.5" />
                  {TEXT.height}
                </div>
                <div className="mt-0.5 break-words text-base font-semibold">{formatValue(heightCm, heightCm ? "cm" : "")}</div>
              </div>
              <div className="min-w-0 rounded-xl border border-white/18 bg-white/12 px-3 py-2">
                <div className="flex items-center gap-1 text-xs opacity-80">
                  <Scale className="h-3.5 w-3.5" />
                  {TEXT.weight}
                </div>
                <div className="mt-0.5 break-words text-base font-semibold">{formatValue(weightKg, weightKg ? "kg" : "")}</div>
              </div>
            </div>

            <div className="min-w-0 rounded-xl border border-white/20 bg-white/12 px-3 py-2 text-base leading-relaxed">
              <div className="opacity-95">{TEXT.checkPrefix}</div>
              <div className="mt-1 flex min-w-0 flex-wrap gap-x-2 gap-y-1 font-bold">
                <span className="break-words">{ward}</span>
                <span className="break-words">{bed}{TEXT.bedSuffix}</span>
                <span className="break-words">{name}</span>
              </div>
              <div className="mt-1 opacity-90">{TEXT.mismatch}</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
