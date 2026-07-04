import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import {
  CheckCheck,
  Loader2,
  MessageSquare,
  Send,
  Stethoscope,
} from "lucide-react"
import { fetchMessages, sendMessage } from "@/lib/api"
import type { PatientMessage } from "@/lib/types"
import { cn } from "@/lib/utils"

interface MessageDialogProps {
  open: boolean
  onOpenChange: (v: boolean) => void
  bed: string
  /** 当前进行中的派送 ID, 留言会自动关联到这次派送 */
  deliveryId?: string
}

const QUICK_QUESTIONS = [
  "这个药要饭前还是饭后吃？",
  "和昨天的药能一起吃吗？",
  "药吃完后有点头晕, 正常吗？",
  "剂量是多少？",
  "可以用温水送服吗？",
  "如果忘记吃了怎么办？",
]

const MAX_LEN = 500

function relTime(seconds: number): string {
  if (!seconds && seconds !== 0) return ""
  const ms = seconds * 1000
  if (!Number.isFinite(ms)) return ""
  const diff = Date.now() - ms
  if (diff < 60_000) return "刚刚"
  if (diff < 3600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86400_000) return `${Math.floor(diff / 3600_000)} 小时前`
  const d = new Date(ms)
  const m = String(d.getMonth() + 1).padStart(2, "0")
  const day = String(d.getDate()).padStart(2, "0")
  const hh = String(d.getHours()).padStart(2, "0")
  const mm = String(d.getMinutes()).padStart(2, "0")
  return `${m}-${day} ${hh}:${mm}`
}

export function MessageDialog({
  open,
  onOpenChange,
  bed,
  deliveryId,
}: MessageDialogProps) {
  const [content, setContent] = useState("")
  const [sending, setSending] = useState(false)
  const [messages, setMessages] = useState<PatientMessage[]>([])
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  // 拉消息列表 (后端 GET 时会自动 mark_thread_read_by_patient)
  const reload = useCallback(async () => {
    if (!bed) return
    const r = await fetchMessages(bed)
    if (r.ok && r.data?.messages) {
      // 后端返回时间倒序, 这里反转一下方便底部追加
      const sorted = [...r.data.messages].sort(
        (a, b) => (a.created_at || 0) - (b.created_at || 0),
      )
      setMessages(sorted)
    }
  }, [bed])

  // 打开时初始加载 + 3 秒轮询
  useEffect(() => {
    if (!open || !bed) return
    let cancelled = false
    setLoading(true)
    reload().finally(() => {
      if (!cancelled) setLoading(false)
    })
    const t = setInterval(reload, 3000)
    return () => {
      cancelled = true
      clearInterval(t)
    }
  }, [open, bed, reload])

  // 消息有变化自动滚到底部
  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages.length, open])

  async function handleSend() {
    const text = content.trim()
    if (!text || sending) return
    setSending(true)
    const r = await sendMessage({
      bed,
      content: text,
      delivery_id: deliveryId,
    })
    setSending(false)
    if (r.ok && r.data?.message) {
      setMessages((prev) => [...prev, r.data!.message])
      setContent("")
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Ctrl/Cmd + Enter 发送
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault()
      void handleSend()
    }
  }

  const trimmed = content.trim()
  const overLimit = content.length > MAX_LEN
  const nurseReplyCount = useMemo(
    () => messages.filter((m) => m.sender === "nurse").length,
    [messages],
  )
  const consultationStatus = useMemo(() => {
    const patientMessages = messages.filter((m) => m.sender === "patient")
    const latestPatient = [...patientMessages].sort(
      (a, b) => (b.created_at || 0) - (a.created_at || 0),
    )[0]
    if (nurseReplyCount > 0) {
      return {
        title: "\u62a4\u58eb\u5df2\u56de\u590d",
        detail: `\u5171 ${nurseReplyCount} \u6b21\u56de\u590d\uff0c\u6709\u65b0\u95ee\u9898\u53ef\u7ee7\u7eed\u8ffd\u95ee\u3002`,
        className: "border-ok/25 bg-ok/10 text-ok",
      }
    }
    if (latestPatient?.read_by_nurse) {
      return {
        title: "\u62a4\u58eb\u5df2\u67e5\u770b",
        detail: "\u60a8\u7684\u95ee\u9898\u5df2\u88ab\u62a4\u58eb\u770b\u5230\uff0c\u8bf7\u7a0d\u7b49\u56de\u590d\u3002",
        className: "border-primary/25 bg-primary-soft/70 text-primary",
      }
    }
    if (latestPatient) {
      return {
        title: "\u54a8\u8be2\u5df2\u9001\u8fbe",
        detail: "\u6d88\u606f\u5df2\u53d1\u5230\u62a4\u58eb\u5de5\u4f5c\u53f0\uff0c\u7cfb\u7edf\u4f1a\u81ea\u52a8\u5237\u65b0\u72b6\u6001\u3002",
        className: "border-border bg-muted/70 text-muted-foreground",
      }
    }
    return null
  }, [messages, nurseReplyCount])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92svh] max-w-md overflow-hidden flex flex-col p-0">
        <DialogHeader className="border-b border-border/60 px-4 pb-3 pt-5 sm:px-6">
          <DialogTitle className="flex min-w-0 items-start gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-primary">
              <MessageSquare className="h-5 w-5" />
            </span>
            咨询护士
          </DialogTitle>
          <DialogDescription>
            您可以询问用药、剂量、不适反应等任何问题, 护士会在工作台上看到并回复
          </DialogDescription>
        </DialogHeader>

        {/* 顶部床位/派送信息 */}
        <div className="flex min-w-0 flex-wrap items-center gap-2 border-b border-border/60 bg-muted/40 px-4 py-2 text-sm sm:px-6">
          <span className="text-muted-foreground">床位</span>
          <strong>{bed || "-"}</strong>
          {deliveryId && (
            <>
              <span className="mx-1 text-muted-foreground">·</span>
              <span className="text-muted-foreground">关联派送</span>
              <span className="min-w-0 break-all font-mono text-xs text-primary">
                {deliveryId}
              </span>
            </>
          )}
          {nurseReplyCount > 0 && (
            <span className="flex items-center gap-1 text-xs text-ok sm:ml-auto">
              <CheckCheck className="h-3.5 w-3.5" />
              护士已回复 {nurseReplyCount} 次
            </span>
          )}
        </div>

        {/* 对话流 */}
        {consultationStatus && (
          <div className={`mx-4 mt-3 rounded-2xl border px-4 py-3 text-sm leading-relaxed ${consultationStatus.className}`}>
            <div className="flex items-center gap-2 font-semibold">
              <CheckCheck className="h-4 w-4" />
              {consultationStatus.title}
            </div>
            <div className="mt-1 text-xs opacity-85">{consultationStatus.detail}</div>
          </div>
        )}

        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto bg-gradient-to-b from-secondary/30 to-background px-3 py-3 space-y-3 sm:px-4"
        >
          {loading ? (
            <div className="flex items-center justify-center py-10 text-muted-foreground">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              加载中...
            </div>
          ) : messages.length === 0 ? (
            <div className="py-10 text-center">
              <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 text-primary">
                <Stethoscope className="h-7 w-7" />
              </div>
              <div className="text-base font-medium">还没有开始对话</div>
              <div className="mt-1 text-sm text-muted-foreground">
                在下方输入您的问题, 护士会尽快回复
              </div>
            </div>
          ) : (
            messages.map((m) => <Bubble key={m.id} msg={m} />)
          )}
        </div>

        {/* 快捷问题 */}
        <div className="border-t border-border/60 bg-card px-3 pb-1 pt-3 sm:px-4">
          <div className="mb-2 text-xs text-muted-foreground">
            常见问题, 点一下加到输入框
          </div>
          <div className="flex min-w-0 flex-wrap gap-1.5">
            {QUICK_QUESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() =>
                  setContent((c) => (c.trim() ? `${c}\n${q}` : q))
                }
                className="rounded-full border border-border bg-card px-3 py-1 text-xs hover:border-primary hover:bg-primary-soft hover:text-primary transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* 输入框 + 发送 */}
        <div className="px-4 pt-2 pb-4 bg-card">
          <div className="flex gap-2 items-end">
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入您要问的问题... (Ctrl+Enter 发送)"
              rows={2}
              className={cn(
                "flex-1 rounded-xl border bg-background px-3 py-2 text-base leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-primary/40 min-h-[60px] max-h-[160px]",
                overLimit
                  ? "border-destructive focus:ring-destructive/40"
                  : "border-border",
              )}
            />
            <Button
              onClick={handleSend}
              disabled={sending || !trimmed || overLimit}
              size="lg"
              className="self-stretch px-4"
            >
              {sending ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </Button>
          </div>
          <div className="mt-1 text-xs flex items-center justify-between">
            <span
              className={cn(
                overLimit ? "text-destructive" : "text-muted-foreground",
              )}
            >
              {content.length} / {MAX_LEN}
            </span>
            <span className="text-muted-foreground">
              每 3 秒自动刷新护士回复
            </span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function Bubble({ msg }: { msg: PatientMessage }) {
  // 系统事件: 居中黄色横条 (病人确认/拒绝等自动回执)
  if (msg.sender === "system") {
    const isAlert = /反馈|拒绝|⚠️/.test(msg.content)
    return (
      <div className="flex justify-center animate-fade-in-up">
        <div
          className={cn(
            "max-w-[92%] px-3 py-1.5 rounded-lg text-xs text-center border border-dashed",
            isAlert
              ? "bg-destructive/10 border-destructive/60 text-destructive"
              : "bg-warn-soft border-warn/40 text-warn-ink",
          )}
        >
          <div className="font-medium">{msg.content}</div>
          <div className="mt-0.5 opacity-70 text-[10px]">
            系统 · {relTime(msg.created_at)}
          </div>
        </div>
      </div>
    )
  }
  const isNurse = msg.sender === "nurse"
  return (
    <div
      className={cn(
        "flex animate-fade-in-up",
        isNurse ? "justify-start" : "justify-end",
      )}
    >
      <div
        className={cn(
          "max-w-[78%] min-w-0",
          isNurse ? "items-start" : "items-end",
        )}
      >
        {isNurse && (
          <div className="mb-1 flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-info-soft text-info-ink">
              <Stethoscope className="h-3 w-3" />
            </span>
            {msg.nurse_name ? `${msg.nurse_name} (护士)` : "护士"}
          </div>
        )}
        <div
          className={cn(
            "px-3.5 py-2 rounded-2xl whitespace-pre-wrap break-words text-base leading-relaxed shadow-soft",
            isNurse
              ? "bg-card border border-border rounded-tl-md text-foreground"
              : "bg-primary text-primary-foreground rounded-tr-md",
          )}
        >
          {msg.content}
        </div>
        <div
          className={cn(
            "mt-1 text-[11px] text-muted-foreground flex items-center gap-1.5",
            isNurse ? "" : "justify-end",
          )}
        >
          {!isNurse && msg.read_by_nurse && (
            <span className="flex items-center gap-0.5 text-ok">
              <CheckCheck className="h-3 w-3" />
              护士已查看
            </span>
          )}
          {!isNurse && !msg.read_by_nurse && (
            <span className="text-muted-foreground">送达</span>
          )}
          <span>{relTime(msg.created_at)}</span>
        </div>
      </div>
    </div>
  )
}
