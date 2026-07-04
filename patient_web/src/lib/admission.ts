export interface AdmissionInfo {
  bed: string
  wardId: string
  wardName: string
  bedNo: string
  patientName: string
}

export const WARD_OPTIONS = [
  { id: "A", name: "A病房" },
  { id: "B", name: "B病房" },
  { id: "C", name: "C病房" },
]

export function wardNameFor(id: string): string {
  const normalized = normalizeWardId(id)
  return WARD_OPTIONS.find((w) => w.id === normalized)?.name || `${normalized}病房`
}

export function normalizeWardId(value: string): string {
  const raw = String(value || "").trim().toUpperCase()
  const match = raw.match(/[A-Z]/)
  return match?.[0] || "A"
}

export function normalizeBedNo(value: string): string {
  const digits = String(value || "").replace(/\D/g, "").slice(0, 2)
  return digits
}

export function makeBedCode(wardId: string, bedNo: string): string {
  const normalizedBed = normalizeBedNo(bedNo)
  const bedPart = normalizedBed ? normalizedBed.padStart(2, "0") : ""
  return bedPart ? `${normalizeWardId(wardId)}-${bedPart}` : ""
}

export function parseBedCode(value: string): Pick<AdmissionInfo, "bed" | "wardId" | "wardName" | "bedNo"> {
  const raw = String(value || "").trim().toUpperCase()
  const wardId = normalizeWardId(raw)
  const bedMatch = raw.match(/(\d{1,2})/)
  const bedNo = normalizeBedNo(bedMatch?.[1] || "")
  const bed = makeBedCode(wardId, bedNo)
  return {
    bed,
    wardId,
    wardName: wardNameFor(wardId),
    bedNo,
  }
}
