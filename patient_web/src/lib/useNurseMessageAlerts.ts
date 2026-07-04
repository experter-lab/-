import { useEffect, useRef } from "react"
import { isQuietHoursActive } from "@/lib/settings"
import type { PatientMessage } from "@/lib/types"

const LS_KEY = "patient_web.lastSeenNurseMsgId"
const TITLE_FLASH_TEXT = "\ud83d\udc8a \u62a4\u58eb\u65b0\u6d88\u606f"

interface Options {
  enabled?: boolean
  suppressed?: boolean
  soundEnabled?: boolean
  browserNotificationEnabled?: boolean
  titleFlashEnabled?: boolean
  quietHoursEnabled?: boolean
}

function lsKeyFor(bed: string) {
  return `${LS_KEY}.${bed || "_default"}`
}

function loadLastSeenId(bed: string): string | null {
  try {
    return localStorage.getItem(lsKeyFor(bed))
  } catch {
    return null
  }
}

function saveLastSeenId(bed: string, id: string) {
  try {
    localStorage.setItem(lsKeyFor(bed), id)
  } catch {
    // ignore quota/private mode errors
  }
}

function playBeep() {
  try {
    const w = window as unknown as {
      AudioContext?: typeof AudioContext
      webkitAudioContext?: typeof AudioContext
    }
    const Ctor = w.AudioContext || w.webkitAudioContext
    if (!Ctor) return
    const ctx = new Ctor()
    const now = ctx.currentTime
    const playTone = (freq: number, start: number, dur: number) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.frequency.value = freq
      osc.type = "sine"
      gain.gain.setValueAtTime(0.0001, now + start)
      gain.gain.exponentialRampToValueAtTime(0.25, now + start + 0.02)
      gain.gain.exponentialRampToValueAtTime(0.0001, now + start + dur)
      osc.connect(gain).connect(ctx.destination)
      osc.start(now + start)
      osc.stop(now + start + dur + 0.05)
    }
    playTone(880, 0.0, 0.15)
    playTone(660, 0.18, 0.18)
    setTimeout(() => ctx.close().catch(() => {}), 800)
  } catch {
    // autoplay/user-gesture restrictions, ignore
  }
}

function fireBrowserNotification(content: string, bed: string) {
  if (typeof Notification === "undefined") return
  const fire = () => {
    try {
      const n = new Notification(`\u62a4\u58eb\u56de\u590d (${bed})`, {
        body: content.slice(0, 80),
        tag: `nurse-${bed}`,
        silent: false,
      })
      setTimeout(() => n.close(), 5000)
      n.onclick = () => {
        window.focus()
        n.close()
      }
    } catch {
      // ignore
    }
  }
  if (Notification.permission === "granted") {
    fire()
  } else if (Notification.permission !== "denied") {
    Notification.requestPermission().then((p) => {
      if (p === "granted") fire()
    }).catch(() => {})
  }
}

const flasher = (() => {
  let originalTitle = ""
  let timer: ReturnType<typeof setInterval> | null = null
  let isFlashing = false

  const stop = () => {
    if (timer) clearInterval(timer)
    timer = null
    if (originalTitle) document.title = originalTitle
    isFlashing = false
  }

  const start = () => {
    if (isFlashing) return
    originalTitle = document.title
    isFlashing = true
    let toggle = false
    timer = setInterval(() => {
      document.title = toggle ? originalTitle : TITLE_FLASH_TEXT
      toggle = !toggle
    }, 1000)
  }

  if (typeof document !== "undefined") {
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) stop()
    })
    window.addEventListener("focus", stop)
  }

  return { start, stop }
})()

export function useNurseMessageAlerts(
  bed: string,
  messages: PatientMessage[],
  options: Options = {},
) {
  const {
    enabled = true,
    suppressed = false,
    soundEnabled = true,
    browserNotificationEnabled = true,
    titleFlashEnabled = true,
    quietHoursEnabled = false,
  } = options
  const baselineSetRef = useRef(false)

  useEffect(() => {
    if (!enabled || !bed) return
    if (!messages || messages.length === 0) return

    const latestNurseMsg = [...messages]
      .filter((m) => m.sender === "nurse")
      .sort((a, b) => (b.created_at || 0) - (a.created_at || 0))[0]
    if (!latestNurseMsg) return

    const lastSeen = loadLastSeenId(bed)

    if (!lastSeen && !baselineSetRef.current) {
      saveLastSeenId(bed, latestNurseMsg.id)
      baselineSetRef.current = true
      return
    }
    baselineSetRef.current = true

    if (lastSeen === latestNurseMsg.id) return

    saveLastSeenId(bed, latestNurseMsg.id)

    if (suppressed) return

    const quietNow = quietHoursEnabled && isQuietHoursActive()

    if (soundEnabled && !quietNow) {
      playBeep()
    }
    if (browserNotificationEnabled && !quietNow) {
      fireBrowserNotification(latestNurseMsg.content, bed)
    }
    if (titleFlashEnabled && !quietNow && (document.hidden || !document.hasFocus())) {
      flasher.start()
    }
  }, [
    bed,
    enabled,
    suppressed,
    messages,
    soundEnabled,
    browserNotificationEnabled,
    titleFlashEnabled,
    quietHoursEnabled,
  ])

  useEffect(() => {
    baselineSetRef.current = false
  }, [bed])
}
