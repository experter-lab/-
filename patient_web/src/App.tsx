import { lazy, Suspense, useState } from "react"
import { BedSetup } from "@/pages/BedSetup"
import { type AdmissionInfo, parseBedCode, wardNameFor } from "@/lib/admission"

const BED_STORAGE_KEY = "patient_web.bed"
const TOKEN_STORAGE_KEY = "patient_web.token"
const ADMISSION_STORAGE_KEY = "patient_web.admission"
const Home = lazy(() => import("@/pages/Home").then((m) => ({ default: m.Home })))

function readInitialSession(): {
  admission: AdmissionInfo | null
  initialBedCode: string
} {
  try {
    const url = new URL(window.location.href)
    const fromToken = url.searchParams.get("t") || url.searchParams.get("token")
    if (fromToken) localStorage.setItem(TOKEN_STORAGE_KEY, fromToken)

    const fromUrl = url.searchParams.get("bed")
    if (fromUrl) {
      const parsed = parseBedCode(fromUrl)
      localStorage.setItem(BED_STORAGE_KEY, parsed.bed)
      return { admission: null, initialBedCode: parsed.bed }
    }

    const storedAdmission = localStorage.getItem(ADMISSION_STORAGE_KEY)
    if (storedAdmission) {
      const parsed = JSON.parse(storedAdmission) as AdmissionInfo
      if (parsed?.bed) return { admission: parsed, initialBedCode: parsed.bed }
    }

    const storedBed = localStorage.getItem(BED_STORAGE_KEY) ?? ""
    if (!storedBed) return { admission: null, initialBedCode: "" }
    const parsed = parseBedCode(storedBed)
    return { admission: null, initialBedCode: parsed.bed }
  } catch {
    return { admission: null, initialBedCode: "" }
  }
}

export default function App() {
  const [session] = useState(readInitialSession)
  const [admission, setAdmission] = useState<AdmissionInfo | null>(
    session.admission,
  )

  function handleConfirmBed(v: AdmissionInfo) {
    const normalized = {
      ...v,
      wardName: v.wardName || wardNameFor(v.wardId),
    }
    localStorage.setItem(BED_STORAGE_KEY, normalized.bed)
    localStorage.setItem(ADMISSION_STORAGE_KEY, JSON.stringify(normalized))
    setAdmission(normalized)
  }

  function handleResetBed() {
    localStorage.removeItem(BED_STORAGE_KEY)
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    localStorage.removeItem(ADMISSION_STORAGE_KEY)
    setAdmission(null)
  }

  if (!admission?.bed) {
    return (
      <BedSetup
        initialBedCode={session.initialBedCode}
        onConfirm={handleConfirmBed}
      />
    )
  }

  return (
    <Suspense
      fallback={
        <div className="app-shell flex min-h-screen items-center justify-center px-4 text-muted-foreground">
          正在加载取药信息...
        </div>
      }
    >
    <Home
      bed={admission.bed}
      admission={admission}
      onResetBed={handleResetBed}
    />
    </Suspense>
  )
}
