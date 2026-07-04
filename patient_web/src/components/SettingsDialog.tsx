import type { ReactNode } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { useSettings } from "@/lib/SettingsContext"
import { FONT_SCALE_LABEL, type FontScale } from "@/lib/settings"
import {
  Bell,
  BellOff,
  BedDouble,
  Building2,
  Cpu,
  Eye,
  Moon,
  RotateCcw,
  Smartphone,
  Sparkles,
  Volume2,
  VolumeX,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface SettingsDialogProps {
  open: boolean
  onOpenChange: (v: boolean) => void
  bed: string
  onResetBed: () => void
}

const FONT_SCALES: FontScale[] = ["small", "medium", "large", "xlarge"]
const TEXT = {
  settings: "\u8bbe\u7f6e",
  settingsDesc: "\u6839\u636e\u60a8\u7684\u4e60\u60ef\u8c03\u6574\u9605\u8bfb\u3001\u64ad\u62a5\u548c\u62a4\u58eb\u56de\u590d\u63d0\u9192\u3002",
  fontSize: "\u5b57\u53f7",
  fontSizeDesc: "\u9009\u62e9\u5408\u9002\u7684\u5b57\u4f53\u5927\u5c0f",
  elderlyMode: "\u8001\u4eba\u6a21\u5f0f",
  elderlyModeDesc: "\u628a\u5173\u952e\u56de\u590d\u63d0\u793a\u653e\u5927\uff0c\u9002\u5408\u8001\u82b1\u773c\u6216\u64cd\u4f5c\u8f83\u6162\u7684\u75c5\u4eba",
  largeReminder: "\u5927\u5b57\u9192\u76ee\u63d0\u9192",
  largeReminderDesc: "\u62a4\u58eb\u6709\u65b0\u56de\u590d\u65f6\uff0c\u5e95\u90e8\u63d0\u793a\u6a2a\u5e45\u4f1a\u66f4\u5927\u3001\u66f4\u660e\u663e\u3002",
  enabled: "\u5df2\u5f00\u542f",
  normal: "\u666e\u901a",
  on: "\u5f00\u542f",
  off: "\u5173\u95ed",
  deliveryNotice: "\u836f\u54c1\u5230\u8fbe\u63d0\u9192",
  deliveryNoticeDesc: "\u914d\u9001\u5230\u8fbe\u65f6\u662f\u5426\u64ad\u653e\u63d0\u793a\u97f3",
  nurseNotice: "\u62a4\u58eb\u56de\u590d\u63d0\u9192",
  nurseNoticeDesc: "\u63a7\u5236\u54a8\u8be2\u6d88\u606f\u7684\u58f0\u97f3\u548c\u624b\u673a\u901a\u77e5",
  sound: "\u63d0\u793a\u97f3",
  soundDesc: "\u62a4\u58eb\u56de\u590d\u65f6\u64ad\u653e\u4e00\u58f0\u77ed\u63d0\u793a\u97f3\u3002",
  browserNotice: "\u624b\u673a/\u6d4f\u89c8\u5668\u901a\u77e5",
  browserNoticeDesc: "\u79bb\u5f00\u9875\u9762\u65f6\uff0c\u7528\u7cfb\u7edf\u901a\u77e5\u63d0\u9192\u62a4\u58eb\u5df2\u56de\u590d\u3002",
  quietHours: "\u591c\u95f4\u514d\u6253\u6270",
  quietHoursDesc: "21:00-07:00 \u4e0d\u5916\u653e\u58f0\u97f3\u3001\u4e0d\u5f39\u7cfb\u7edf\u901a\u77e5\uff0c\u9875\u9762\u5185\u4ecd\u4f1a\u9192\u76ee\u63d0\u793a\u3002",
  bed: "\u5e8a\u4f4d",
  currentBed: "\u5f53\u524d\u5e8a\u4f4d",
  switchBed: "\u5207\u6362\u5e8a\u4f4d",
  about: "\u5173\u4e8e",
  department: "\u79d1\u5ba4",
  departmentValue: "\u5185\u79d1\u75c5\u623f\u697c",
  version: "\u7248\u672c",
  device: "\u8bbe\u5907",
}

export function SettingsDialog({
  open,
  onOpenChange,
  bed,
  onResetBed,
}: SettingsDialogProps) {
  const settings = useSettings()

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[88svh] max-w-md overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{TEXT.settings}</DialogTitle>
          <DialogDescription>{TEXT.settingsDesc}</DialogDescription>
        </DialogHeader>

        <div className="space-y-5">
          <Section icon={<Sparkles className="h-4 w-4" />} title={TEXT.fontSize} desc={TEXT.fontSizeDesc}>
            <div className="grid min-w-0 grid-cols-2 gap-2 sm:grid-cols-4">
              {FONT_SCALES.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => settings.setFontScale(s)}
                  className={cn(
                    "flex min-h-16 flex-col items-center justify-center rounded-xl border-2 px-2 py-3 transition-colors",
                    settings.fontScale === s
                      ? "border-primary bg-primary/10"
                      : "border-border hover:bg-accent",
                  )}
                >
                  <span
                    className={cn(
                      "font-bold leading-none",
                      s === "small" && "text-base",
                      s === "medium" && "text-lg",
                      s === "large" && "text-xl",
                      s === "xlarge" && "text-2xl",
                    )}
                  >
                    A
                  </span>
                  <span className="mt-1.5 text-xs text-muted-foreground">
                    {FONT_SCALE_LABEL[s]}
                  </span>
                </button>
              ))}
            </div>
          </Section>

          <Section
            icon={<Eye className="h-4 w-4" />}
            title={TEXT.elderlyMode}
            desc={TEXT.elderlyModeDesc}
          >
            <ToggleRow
              label={TEXT.largeReminder}
              desc={TEXT.largeReminderDesc}
              checked={settings.elderlyModeEnabled}
              onChange={settings.setElderlyModeEnabled}
              onText={TEXT.enabled}
              offText={TEXT.normal}
            />
          </Section>

          <Section
            icon={settings.notificationEnabled ? <Bell className="h-4 w-4" /> : <BellOff className="h-4 w-4" />}
            title={TEXT.deliveryNotice}
            desc={TEXT.deliveryNoticeDesc}
          >
            <TwoButtonToggle
              value={settings.notificationEnabled}
              onChange={settings.setNotificationEnabled}
              trueText={TEXT.on}
              falseText={TEXT.off}
            />
          </Section>

          <Section
            icon={settings.nurseAlertSoundEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
            title={TEXT.nurseNotice}
            desc={TEXT.nurseNoticeDesc}
          >
            <div className="space-y-2.5">
              <ToggleRow
                label={TEXT.sound}
                desc={TEXT.soundDesc}
                checked={settings.nurseAlertSoundEnabled}
                onChange={settings.setNurseAlertSoundEnabled}
              />
              <ToggleRow
                label={TEXT.browserNotice}
                desc={TEXT.browserNoticeDesc}
                checked={settings.nurseBrowserNotificationEnabled}
                onChange={settings.setNurseBrowserNotificationEnabled}
                icon={<Smartphone className="h-4 w-4" />}
              />
              <ToggleRow
                label={TEXT.quietHours}
                desc={TEXT.quietHoursDesc}
                checked={settings.quietHoursEnabled}
                onChange={settings.setQuietHoursEnabled}
                icon={<Moon className="h-4 w-4" />}
              />
            </div>
          </Section>

          <Section icon={<BedDouble className="h-4 w-4" />} title={TEXT.bed} desc={`${TEXT.currentBed}: ${bed}`}>
            <Button
              variant="outline"
              onClick={() => {
                onOpenChange(false)
                onResetBed()
              }}
              className="w-full gap-2"
            >
              <RotateCcw className="h-4 w-4" />
              {TEXT.switchBed}
            </Button>
          </Section>

          <Section icon={<Building2 className="h-4 w-4" />} title={TEXT.about}>
            <div className="space-y-1.5 rounded-xl bg-muted/60 p-3 text-sm">
              <Row label={TEXT.department} value={TEXT.departmentValue} />
              <Row label={TEXT.version} value="v0.2.1" />
              <Row
                label={TEXT.device}
                value={
                  <span className="inline-flex min-w-0 items-center gap-1 break-all font-mono text-xs">
                    <Cpu className="h-3 w-3" />
                    PWB-{bed.padStart(4, "0")}
                  </span>
                }
              />
            </div>
          </Section>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function Section({
  icon,
  title,
  desc,
  children,
}: {
  icon: ReactNode
  title: string
  desc?: string
  children?: ReactNode
}) {
  return (
    <section className="space-y-2.5">
      <div className="flex items-start gap-2">
        <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
          {icon}
        </span>
        <div className="min-w-0 flex-1">
          <div className="font-semibold leading-tight">{title}</div>
          {desc && <div className="mt-0.5 text-xs leading-relaxed text-muted-foreground">{desc}</div>}
        </div>
      </div>
      {children}
    </section>
  )
}

function TwoButtonToggle({
  value,
  onChange,
  trueText,
  falseText,
}: {
  value: boolean
  onChange: (v: boolean) => void
  trueText: string
  falseText: string
}) {
  return (
    <div className="flex min-w-0 gap-2">
      <Button
        variant={value ? "default" : "outline"}
        onClick={() => onChange(true)}
        className="min-w-0 flex-1 px-2 whitespace-normal"
      >
        {trueText}
      </Button>
      <Button
        variant={!value ? "default" : "outline"}
        onClick={() => onChange(false)}
        className="min-w-0 flex-1 px-2 whitespace-normal"
      >
        {falseText}
      </Button>
    </div>
  )
}

function ToggleRow({
  label,
  desc,
  checked,
  onChange,
  icon,
  onText = TEXT.on,
  offText = TEXT.off,
}: {
  label: string
  desc: string
  checked: boolean
  onChange: (v: boolean) => void
  icon?: ReactNode
  onText?: string
  offText?: string
}) {
  return (
    <div className="rounded-2xl border border-border/80 bg-card/70 p-3">
      <div className="flex items-start gap-3">
        {icon && (
          <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
            {icon}
          </span>
        )}
        <div className="min-w-0 flex-1">
          <div className="font-semibold leading-tight">{label}</div>
          <div className="mt-1 text-sm leading-relaxed text-muted-foreground">{desc}</div>
        </div>
      </div>
      <div className="mt-3 flex min-w-0 gap-2">
        <Button
          size="sm"
          variant={checked ? "default" : "outline"}
          onClick={() => onChange(true)}
          className="min-w-0 flex-1 px-2 whitespace-normal"
        >
          {onText}
        </Button>
        <Button
          size="sm"
          variant={!checked ? "default" : "outline"}
          onClick={() => onChange(false)}
          className="min-w-0 flex-1 px-2 whitespace-normal"
        >
          {offText}
        </Button>
      </div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex min-w-0 items-center justify-between gap-3">
      <span className="text-muted-foreground">{label}</span>
      <span className="min-w-0 break-words text-right font-medium">{value}</span>
    </div>
  )
}
