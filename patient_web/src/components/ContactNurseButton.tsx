import { useEffect, useMemo, useState } from "react"
import { Button } from "@/components/ui/button"
import { Loader2, MessageCircleQuestion, Mic } from "lucide-react"
import { fetchMessages, startVoiceListen } from "@/lib/api"
import { useSettings } from "@/lib/SettingsContext"
import { useNurseMessageAlerts } from "@/lib/useNurseMessageAlerts"
import { cn } from "@/lib/utils"
import type { PatientMessage } from "@/lib/types"

interface ContactNurseButtonProps {
  bed: string
  onClick: () => void
  refreshKey?: number
  dialogOpen?: boolean
  deliveryId?: string
}

const VOICE_LISTEN_DURATION_SEC = 300
const TEXT = {
  voiceOpening: "\u6b63\u5728\u5f00\u542f\u95ee\u836f\u8bed\u97f3\u52a9\u624b\uff0c\u8bf7\u7a0d\u5019\u3002",
  voiceOpened: "\u95ee\u836f\u8bed\u97f3\u52a9\u624b\u5df2\u5f00\u542f 5 \u5206\u949f\u3002\u60a8\u53ef\u4ee5\u76f4\u63a5\u95ee\uff1a\u8fd9\u4e2a\u836f\u600e\u4e48\u5403\u3001\u6709\u4ec0\u4e48\u6ce8\u610f\u4e8b\u9879\u3001\u5fd8\u8bb0\u5403\u4e86\u600e\u4e48\u529e\u3002",
  voiceFailed: "\u95ee\u836f\u8bed\u97f3\u52a9\u624b\u5f00\u542f\u5931\u8d25\uff0c\u8bf7\u5148\u4f7f\u7528\u6587\u5b57\u54a8\u8be2\u62a4\u58eb\u3002",
  nurseRepliedOpen: "\u62a4\u58eb\u5df2\u56de\u590d\uff0c\u8bf7\u70b9\u5f00\u67e5\u770b",
  nurseReplies: "\u5df2\u6709\u62a4\u58eb\u56de\u590d",
  times: "\u6b21",
  nurseRead: "\u62a4\u58eb\u5df2\u67e5\u770b\uff0c\u6b63\u5728\u5904\u7406",
  sent: "\u54a8\u8be2\u5df2\u9001\u8fbe\uff0c\u7b49\u5f85\u62a4\u58eb\u67e5\u770b",
  askNurseAnytime: "\u6709\u7591\u95ee\u53ef\u968f\u65f6\u54a8\u8be2\u62a4\u58eb",
  nurseNewReply: "\u62a4\u58eb\u6709\u65b0\u56de\u590d",
  clickToView: "\u70b9\u51fb\u67e5\u770b\u62a4\u58eb\u7684\u56de\u590d\uff0c\u672a\u8bfb",
  item: "\u6761",
  view: "\u67e5\u770b",
  quietHint: "\u591c\u95f4\u514d\u6253\u6270\u5f00\u542f\u65f6\uff0c\u9875\u9762\u4ecd\u4f1a\u4fdd\u7559\u9192\u76ee\u63d0\u793a\u3002",
  consultNurse: "\u54a8\u8be2\u62a4\u58eb",
  medicineVoice: "\u95ee\u836f\u8bed\u97f3 5\u5206\u949f",
  medicineVoiceActive: "\u95ee\u836f\u4e2d",
  voiceAria: "\u5f00\u542f\u95ee\u836f\u8bed\u97f3\u52a9\u624b\u4e94\u5206\u949f",
}

function formatVoiceCountdown(seconds: number) {
  const safeSeconds = Math.max(0, Math.floor(seconds))
  const minutes = Math.floor(safeSeconds / 60)
  const restSeconds = safeSeconds % 60
  return `${minutes}:${String(restSeconds).padStart(2, "0")}`
}

export function ContactNurseButton({
  bed,
  onClick,
  refreshKey,
  dialogOpen = false,
  deliveryId,
}: ContactNurseButtonProps) {
  const settings = useSettings()
  const [unreadFromNurse, setUnreadFromNurse] = useState(0)
  const [messages, setMessages] = useState<PatientMessage[]>([])
  const [voiceRemaining, setVoiceRemaining] = useState(0)
  const [voiceBusy, setVoiceBusy] = useState(false)
  const [voiceMessage, setVoiceMessage] = useState("")

  useEffect(() => {
    if (!bed) return
    let cancelled = false
    const pull = async () => {
      try {
        const r = await fetchMessages(bed, { markRead: false })
        if (cancelled) return
        if (r.ok && r.data?.messages) {
          const msgs = r.data.messages
          setMessages(msgs)
          setUnreadFromNurse(
            msgs.filter((m) => m.sender === "nurse" && !m.read_by_patient).length,
          )
        }
      } catch {
        // ignore polling failures
      }
    }
    void pull()
    const t = setInterval(pull, 5000)
    return () => {
      cancelled = true
      clearInterval(t)
    }
  }, [bed, refreshKey])

  useEffect(() => {
    if (voiceRemaining <= 0) return
    const t = window.setInterval(() => {
      setVoiceRemaining((v) => Math.max(0, v - 1))
    }, 1000)
    return () => window.clearInterval(t)
  }, [voiceRemaining])

  async function handleVoiceListen() {
    if (voiceBusy || voiceRemaining > 0) return
    setVoiceBusy(true)
    setVoiceMessage(TEXT.voiceOpening)
    const r = await startVoiceListen({
      bed,
      delivery_id: deliveryId,
      duration_sec: VOICE_LISTEN_DURATION_SEC,
    })
    setVoiceBusy(false)
    if (r.ok) {
      const duration = Number(r.data?.duration_sec || VOICE_LISTEN_DURATION_SEC)
      setVoiceRemaining(duration)
      setVoiceMessage(TEXT.voiceOpened)
    } else {
      setVoiceMessage(r.error || TEXT.voiceFailed)
    }
  }

  useNurseMessageAlerts(bed, messages, {
    enabled: true,
    suppressed: dialogOpen,
    soundEnabled: settings.nurseAlertSoundEnabled,
    browserNotificationEnabled: settings.nurseBrowserNotificationEnabled,
    titleFlashEnabled: settings.nurseBrowserNotificationEnabled,
    quietHoursEnabled: settings.quietHoursEnabled,
  })

  const consultationStatus = useMemo(() => {
    const patientMessages = messages.filter((m) => m.sender === "patient")
    const nurseMessages = messages.filter((m) => m.sender === "nurse")
    const latestPatient = [...patientMessages].sort(
      (a, b) => (b.created_at || 0) - (a.created_at || 0),
    )[0]
    if (unreadFromNurse > 0) {
      return {
        label: TEXT.nurseRepliedOpen,
        className: "border-ok/30 bg-ok/10 text-ok",
      }
    }
    if (nurseMessages.length > 0) {
      return {
        label: `${TEXT.nurseReplies} ${nurseMessages.length} ${TEXT.times}`,
        className: "border-ok/25 bg-ok/8 text-ok",
      }
    }
    if (latestPatient?.read_by_nurse) {
      return {
        label: TEXT.nurseRead,
        className: "border-primary/25 bg-primary-soft/60 text-primary",
      }
    }
    if (latestPatient) {
      return {
        label: TEXT.sent,
        className: "border-border bg-muted/70 text-muted-foreground",
      }
    }
    return {
      label: TEXT.askNurseAnytime,
      className: "border-border bg-background/80 text-muted-foreground",
    }
  }, [messages, unreadFromNurse])

  const elderlyMode = settings.elderlyModeEnabled

  return (
    <div className="sticky bottom-0 left-0 right-0 mt-4 -mx-3 border-t border-border/70 surface-glass px-3 pb-4 pt-3">
      <div className="relative">
        {unreadFromNurse > 0 && (
          <span
            aria-hidden
            className="absolute -inset-1 rounded-2xl bg-primary/20 blur-md animate-soft-pulse"
          />
        )}
        {unreadFromNurse > 0 && (
          <button
            type="button"
            onClick={onClick}
            role="alert"
            aria-live="assertive"
            className={cn(
              "relative mb-2 flex w-full items-center justify-between gap-3 rounded-2xl border-2 border-ok/30 bg-ok/12 text-left shadow-soft ring-2 ring-ok/10 animate-soft-pulse",
              elderlyMode ? "px-5 py-4 shadow-elevated" : "px-4 py-3",
            )}
            aria-label={TEXT.nurseNewReply}
          >
            <span className="flex min-w-0 flex-col">
              <span className={cn("font-extrabold leading-tight text-ok", elderlyMode ? "text-xl" : "text-lg")}>
                {TEXT.nurseNewReply}
              </span>
              <span className={cn("mt-0.5 font-semibold text-ok/85", elderlyMode ? "text-base" : "text-sm")}>
                {TEXT.clickToView} {unreadFromNurse} {TEXT.item}
              </span>
              {settings.quietHoursEnabled && (
                <span className="mt-1 text-xs font-medium text-ok/70">
                  {TEXT.quietHint}
                </span>
              )}
            </span>
            <span className={cn("shrink-0 rounded-full bg-ok font-bold text-white", elderlyMode ? "px-4 py-2 text-base" : "px-3 py-1.5 text-sm")}>
              {TEXT.view}
            </span>
          </button>
        )}
        <div className="grid grid-cols-1 gap-2 min-[390px]:grid-cols-2">
          <Button
            size="lg"
            className={cn(
              "relative h-auto min-h-14 w-full rounded-2xl px-3 py-2 font-semibold whitespace-normal shadow-glow",
              elderlyMode ? "min-h-16 text-lg" : "text-base sm:text-lg",
            )}
            onClick={onClick}
            aria-label={TEXT.consultNurse}
          >
            <MessageCircleQuestion className="mr-1.5 h-5 w-5 shrink-0" />
            <span className="min-w-0 break-words leading-snug">{TEXT.consultNurse}</span>
            {unreadFromNurse > 0 && (
              <span className="absolute -right-2 -top-2 inline-flex h-7 min-w-7 items-center justify-center rounded-full border-2 border-white bg-destructive px-2 text-xs font-bold text-destructive-foreground shadow-lg">
                {unreadFromNurse > 99 ? "99+" : unreadFromNurse}
              </span>
            )}
          </Button>
          <Button
            size="lg"
            variant="outline"
            className={cn(
              "h-auto min-h-14 w-full rounded-2xl border-2 bg-background/85 px-3 py-2 font-semibold whitespace-normal",
              elderlyMode ? "min-h-16 text-lg" : "text-base sm:text-lg",
            )}
            onClick={handleVoiceListen}
            disabled={voiceBusy || voiceRemaining > 0}
            aria-label={TEXT.voiceAria}
          >
            {voiceBusy ? (
              <Loader2 className="mr-1.5 h-5 w-5 shrink-0 animate-spin" />
            ) : (
              <Mic className="mr-1.5 h-5 w-5 shrink-0" />
            )}
            <span className="min-w-0 break-words leading-snug">
              {voiceRemaining > 0 ? `${TEXT.medicineVoiceActive} ${formatVoiceCountdown(voiceRemaining)}` : TEXT.medicineVoice}
            </span>
          </Button>
        </div>
        <div className={cn(
          "mt-2 rounded-xl border px-3 py-2 font-medium leading-relaxed",
          elderlyMode ? "text-base" : "text-sm",
          consultationStatus.className,
        )}>
          {consultationStatus.label}
        </div>
        {voiceMessage && (
          <div className={cn(
            "mt-2 rounded-xl border border-primary/20 bg-primary-soft/60 px-3 py-2 font-medium leading-relaxed text-primary",
            elderlyMode ? "text-lg" : "text-base",
          )}>
            {voiceMessage}
          </div>
        )}
      </div>
    </div>
  )
}
