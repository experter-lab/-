// 后端 API 客户端 - mock / 真实后端切换
import type {
  ApiResult,
  CallRobotRequest,
  PatientDelivery,
  PatientIdentity,
  PatientHistoryEntry,
  PatientMessage,
  RobotStatus,
  SendMessageRequest,
} from "./types"
import { MOCK_CURRENT_DELIVERY, MOCK_HISTORY } from "./mock"

const USE_MOCK = false  // 接入真实后端时改 false
const TOKEN_STORAGE_KEY = "patient_web.token"

function delay<T>(value: T, ms = 300): Promise<T> {
  return new Promise((r) => setTimeout(() => r(value), ms))
}

function readPatientToken(): string {
  try {
    const url = new URL(window.location.href)
    const fromUrl = url.searchParams.get("t") || url.searchParams.get("token")
    if (fromUrl) {
      localStorage.setItem(TOKEN_STORAGE_KEY, fromUrl)
      return fromUrl
    }
    return localStorage.getItem(TOKEN_STORAGE_KEY) ?? ""
  } catch {
    return ""
  }
}

function withPatientToken(path: string): string {
  const token = readPatientToken()
  if (!token) return path
  const sep = path.includes("?") ? "&" : "?"
  return `${path}${sep}t=${encodeURIComponent(token)}`
}

function patientHeaders(
  headers: Record<string, string> = {},
): Record<string, string> {
  const token = readPatientToken()
  if (!token) return headers
  return { ...headers, "X-Patient-Token": token }
}


async function requestJson<T = unknown>(
  input: RequestInfo | URL,
  init: RequestInit = {},
  timeoutMs = 8000,
): Promise<ApiResult<T>> {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeoutMs)
  try {
    const res = await fetch(input, { ...init, signal: controller.signal })
    let payload: unknown = null
    try {
      payload = await res.json()
    } catch {
      payload = null
    }
    if (!res.ok) {
      const message =
        payload && typeof payload === "object" && "error" in payload
          ? String((payload as { error?: unknown }).error || "")
          : payload && typeof payload === "object" && "message" in payload
            ? String((payload as { message?: unknown }).message || "")
            : `请求失败：${res.status}`
      return { ok: false, error: message || `请求失败：${res.status}` }
    }
    if (payload && typeof payload === "object" && "ok" in payload) {
      return payload as ApiResult<T>
    }
    return { ok: true, data: payload as T }
  } catch (error) {
    const aborted = error instanceof DOMException && error.name === "AbortError"
    return {
      ok: false,
      error: aborted ? "网络响应超时，请稍后重试。" : error instanceof Error ? error.message : "网络连接异常，请稍后重试。",
    }
  } finally {
    window.clearTimeout(timer)
  }
}

export async function fetchCurrentDelivery(
  bed: string,
): Promise<ApiResult<PatientDelivery | null>> {
  if (USE_MOCK) {
    if (bed === MOCK_CURRENT_DELIVERY.bed)
      return delay({ ok: true, data: MOCK_CURRENT_DELIVERY })
    return delay({ ok: true, data: null })
  }
  return requestJson<PatientDelivery | null>(
    withPatientToken(`/patient/api/delivery?bed=${encodeURIComponent(bed)}`),
  )
}

export async function fetchIdentity(
  bed: string,
): Promise<ApiResult<PatientIdentity>> {
  if (USE_MOCK) {
    return delay({
      ok: true,
      data: {
        bed,
        ward: "A病房",
        patient_name: "张三",
        has_delivery: true,
        delivery_id: `PWB-${bed}-20260621`,
      },
    })
  }
  return requestJson<PatientIdentity>(
    withPatientToken(`/patient/api/identity?bed=${encodeURIComponent(bed)}`),
  )
}

export async function fetchHistory(
  bed: string,
  days = 7,
): Promise<ApiResult<PatientHistoryEntry[]>> {
  if (USE_MOCK) {
    void bed
    void days
    return delay({ ok: true, data: MOCK_HISTORY })
  }
  return requestJson<PatientHistoryEntry[]>(
    withPatientToken(
      `/patient/api/history?bed=${encodeURIComponent(bed)}&days=${days}`,
    ),
  )
}

export async function confirmDelivery(
  deliveryId: string,
  bed: string,
): Promise<ApiResult> {
  if (USE_MOCK) {
    void bed
    return delay({ ok: true })
  }
  return requestJson(`/patient/api/deliveries/${encodeURIComponent(deliveryId)}/confirm`, {
    method: "POST",
    headers: patientHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ bed }),
  })
}

export async function rejectDelivery(
  deliveryId: string,
  reason: string,
  bed: string,
): Promise<ApiResult> {
  if (USE_MOCK) {
    void reason
    void bed
    return delay({ ok: true })
  }
  return requestJson(`/patient/api/deliveries/${encodeURIComponent(deliveryId)}/reject`, {
    method: "POST",
    headers: patientHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ reason, bed }),
  })
}

export async function callRobot(req: CallRobotRequest): Promise<ApiResult> {
  if (USE_MOCK) return delay({ ok: true })
  return requestJson(`/patient/api/call_robot`, {
    method: "POST",
    headers: patientHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(req),
  })
}

export async function fetchMessages(
  bed: string,
  options: { markRead?: boolean } = {},
): Promise<ApiResult<{ bed: string; messages: PatientMessage[] }>> {
  if (USE_MOCK) return delay({ ok: true, data: { bed, messages: [] } })
  const markRead = options.markRead === false ? "0" : "1"
  return requestJson<{ bed: string; messages: PatientMessage[] }>(
    withPatientToken(
      `/patient/api/messages?bed=${encodeURIComponent(bed)}&mark_read=${markRead}`,
    ),
  )
}

export async function sendMessage(
  req: SendMessageRequest,
): Promise<ApiResult<{ message: PatientMessage }>> {
  if (USE_MOCK) {
    return delay({
      ok: true,
      data: {
        message: {
          id: `mock-${Date.now()}`,
          bed: req.bed,
          sender: "patient",
          content: req.content,
          delivery_id: req.delivery_id,
          created_at: Date.now() / 1000,
          read_by_patient: true,
          read_by_nurse: false,
        },
      },
    })
  }
  return requestJson<{ message: PatientMessage }>(`/patient/api/messages`, {
    method: "POST",
    headers: patientHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(req),
  })
}


export async function startVoiceListen(req: {
  bed: string
  delivery_id?: string
  duration_sec?: number
}): Promise<ApiResult<{ duration_sec?: number; subscribers?: number }>> {
  if (USE_MOCK) return delay({ ok: true, data: { duration_sec: req.duration_sec ?? 300 } })
  return requestJson<{ duration_sec?: number; subscribers?: number }>(`/patient/api/voice/listen`, {
    method: "POST",
    headers: patientHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(req),
  }, 12000)
}
export async function announceVoice(req: {
  text: string
  bed?: string
  delivery_id?: string
}): Promise<ApiResult<{ text: string; subscribers?: number }>> {
  if (USE_MOCK) return delay({ ok: true, data: { text: req.text } })
  return requestJson<{ text: string; subscribers?: number }>(`/patient/api/voice/announce`, {
    method: "POST",
    headers: patientHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(req),
  }, 12000)
}

export async function fetchRobotStatus(
  bed: string,
): Promise<ApiResult<RobotStatus>> {
  if (USE_MOCK) {
    return delay({
      ok: true,
      data: {
        bed,
        task_id: "",
        task_state: "IDLE",
        task_bed: "",
        current_station: "pharmacy",
        current_station_name: "药房",
        target_station: "",
        target_station_name: "",
        for_me: false,
        stage: "idle",
        human_text: "机器人在药房待命",
        chassis_ok: true,
        stamp: Date.now() / 1000,
      },
    })
  }
  return requestJson<RobotStatus>(
    withPatientToken(`/patient/api/robot_status?bed=${encodeURIComponent(bed)}`),
  )
}
