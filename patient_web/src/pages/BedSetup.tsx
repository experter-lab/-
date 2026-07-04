import { useEffect, useMemo, useState } from "react"
import { AppHeader } from "@/components/AppHeader"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { fetchIdentity } from "@/lib/api"
import {
  makeBedCode,
  normalizeBedNo,
  type AdmissionInfo,
  WARD_OPTIONS,
  wardNameFor,
} from "@/lib/admission"
import {
  BedDouble,
  Building2,
  CheckCircle2,
  Loader2,
  UserRound,
} from "lucide-react"

interface BedSetupProps {
  initialBedCode?: string
  onConfirm: (payload: AdmissionInfo) => void
}

function parseInitialBed(value: string): { wardId: string; bedNo: string } {
  const raw = String(value || "").trim().toUpperCase()
  const wardMatch = raw.match(/[A-Z]/)
  const bedMatch = raw.match(/(\d{1,2})/)
  return {
    wardId: wardMatch?.[0] || "A",
    bedNo: normalizeBedNo(bedMatch?.[1] || ""),
  }
}

export function BedSetup({ initialBedCode = "", onConfirm }: BedSetupProps) {
  const initial = useMemo(() => parseInitialBed(initialBedCode), [initialBedCode])
  const [wardId, setWardId] = useState(initial.wardId)
  const [bedNo, setBedNo] = useState(initial.bedNo)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [identity, setIdentity] = useState<AdmissionInfo | null>(null)

  const bed = makeBedCode(wardId, bedNo)
  const wardName = wardNameFor(wardId)

  useEffect(() => {
    if (initialBedCode) {
      setWardId(initial.wardId)
      setBedNo(initial.bedNo)
    }
  }, [initialBedCode, initial.bedNo, initial.wardId])

  useEffect(() => {
    setIdentity(null)
    setError("")
  }, [wardId, bedNo])

  async function queryIdentity() {
    const normalizedBed = makeBedCode(wardId, bedNo)
    if (!normalizedBed) {
      setError("请先输入完整床号")
      return
    }
    setLoading(true)
    setError("")
    setIdentity(null)
    try {
      const res = await fetchIdentity(normalizedBed)
      if (!res.ok || !res.data) {
        setError(res.error || "未查询到床位身份")
        return
      }
      setIdentity({
        bed: res.data.bed || normalizedBed,
        wardId,
        wardName: res.data.ward || wardName,
        bedNo,
        patientName: res.data.patient_name || "",
      })
    } finally {
      setLoading(false)
    }
  }

  function confirmIdentity() {
    if (!identity) return
    onConfirm(identity)
  }

  const canQuery = Boolean(bed) && !loading

  return (
    <div className="min-h-screen flex flex-col">
      <AppHeader subtitle="取药终端" />

      <main className="app-shell flex-1 space-y-5 px-3 pb-8 pt-4 sm:pt-5">
        <section className="space-y-2 text-center sm:space-y-3">
          <div className="text-2xl font-black tracking-tight text-foreground sm:text-3xl">
            欢迎使用取药终端
          </div>
          <div className="mx-auto max-w-[24rem] text-base leading-relaxed text-muted-foreground sm:text-lg">
            先确认病房和床号，再由系统核对姓名
          </div>
        </section>

        <Card className="rounded-2xl shadow-card">
          <CardHeader className="space-y-2 p-4 sm:p-6">
            <CardDescription>第一步</CardDescription>
            <CardTitle className="break-words text-xl sm:text-2xl">请输入病房和床号</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 p-4 pt-0 sm:space-y-5 sm:p-6 sm:pt-0">
            <div className="grid gap-3 sm:grid-cols-3">
              {WARD_OPTIONS.map((ward) => {
                const active = ward.id === wardId
                return (
                  <Button
                    key={ward.id}
                    type="button"
                    variant={active ? "default" : "outline"}
                    className="h-auto min-h-14 justify-start px-4 py-2 text-base whitespace-normal"
                    onClick={() => setWardId(ward.id)}
                  >
                    <Building2 className="h-5 w-5" />
                    <span className="min-w-0 break-words font-semibold">{ward.name}</span>
                  </Button>
                )
              })}
            </div>

            <div className="grid gap-3 sm:grid-cols-[1fr_160px]">
              <div className="space-y-2">
                <div className="text-sm font-medium text-muted-foreground">
                  床号
                </div>
                <Input
                  inputMode="numeric"
                  value={bedNo}
                  maxLength={2}
                  placeholder="例如 02"
                  onChange={(e) => setBedNo(normalizeBedNo(e.target.value))}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault()
                      void queryIdentity()
                    }
                  }}
                />
              </div>
              <div className="space-y-2">
                <div className="text-sm font-medium text-muted-foreground">
                  当前床位
                </div>
                <div className="flex h-14 min-w-0 items-center rounded-lg border border-border bg-muted/50 px-4 text-lg font-semibold tracking-wider">
                  {bed || "A-__"}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2">
              {["1", "2", "3", "4", "5", "6", "7", "8", "9"].map((n) => (
                <Button
                  key={n}
                  type="button"
                  variant="outline"
                  className="h-14 text-xl font-semibold"
                  onClick={() =>
                    setBedNo((prev) => normalizeBedNo((prev + n).slice(0, 2)))
                  }
                >
                  {n}
                </Button>
              ))}
              <Button
                type="button"
                variant="secondary"
                className="h-14 text-lg font-semibold"
                onClick={() => setBedNo("")}
              >
                清空
              </Button>
              <Button
                type="button"
                variant="outline"
                className="h-14 text-xl font-semibold"
                onClick={() => setBedNo((prev) => prev.slice(0, -1))}
              >
                0
              </Button>
              <Button
                type="button"
                variant="secondary"
                className="h-14 text-lg font-semibold"
                onClick={() => setBedNo((prev) => normalizeBedNo(prev))}
              >
                确认
              </Button>
            </div>

            <div className="rounded-xl border border-border bg-secondary/40 px-3 py-3 text-sm leading-relaxed text-muted-foreground sm:px-4">
              先选病房，再输床号。系统会根据床位返回病房名和姓名，不再手填姓名。
            </div>

            {error ? (
              <div className="rounded-xl border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
                {error}
              </div>
            ) : null}

            {identity ? (
              <div className="grid min-w-0 gap-3 rounded-2xl border border-primary/20 bg-primary/5 p-3 sm:grid-cols-3 sm:p-4">
                <div className="flex min-w-0 items-center gap-3 rounded-xl bg-background px-3 py-3 sm:px-4">
                  <Building2 className="h-5 w-5 text-primary" />
                  <div>
                    <div className="text-xs text-muted-foreground">病房</div>
                    <div className="break-words font-semibold">{identity.wardName}</div>
                  </div>
                </div>
                <div className="flex min-w-0 items-center gap-3 rounded-xl bg-background px-3 py-3 sm:px-4">
                  <BedDouble className="h-5 w-5 text-primary" />
                  <div>
                    <div className="text-xs text-muted-foreground">床号</div>
                    <div className="break-words font-semibold">{identity.bed}</div>
                  </div>
                </div>
                <div className="flex min-w-0 items-center gap-3 rounded-xl bg-background px-3 py-3 sm:px-4">
                  <UserRound className="h-5 w-5 text-primary" />
                  <div>
                    <div className="text-xs text-muted-foreground">姓名</div>
                    <div className="break-words font-semibold">
                      {identity.patientName || "未返回姓名"}
                    </div>
                  </div>
                </div>
              </div>
            ) : null}

            {!identity ? (
              <Button
                type="button"
                className="h-auto min-h-14 w-full px-3 py-2 text-lg font-semibold whitespace-normal"
                onClick={() => void queryIdentity()}
                disabled={!canQuery}
              >
                {loading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    查询身份
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="h-5 w-5" />
                    查询身份
                  </>
                )}
              </Button>
            ) : (
              <Button
                type="button"
                className="h-auto min-h-14 w-full px-3 py-2 text-lg font-semibold whitespace-normal"
                onClick={confirmIdentity}
              >
                <CheckCircle2 className="h-5 w-5" />
                是本人，进入
              </Button>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
