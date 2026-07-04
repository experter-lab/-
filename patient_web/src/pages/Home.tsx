import { useCallback, useEffect, useState } from "react"
import { AppHeader } from "@/components/AppHeader"
import { HeroCard } from "@/components/HeroCard"
import { DeliveryCard } from "@/components/DeliveryCard"
import { HistoryList } from "@/components/HistoryList"
import { ContactNurseButton } from "@/components/ContactNurseButton"
import { RobotStatusCard } from "@/components/RobotStatusCard"
import { HealthAlertCard } from "@/components/HealthAlertCard"
import { ReportIssueCard } from "@/components/ReportIssueCard"
import { EmptyOrder } from "@/components/EmptyOrder"
import { SettingsDialog } from "@/components/SettingsDialog"
import { NotificationsDialog } from "@/components/NotificationsDialog"
import { MessageDialog } from "@/components/MessageDialog"
import { fetchCurrentDelivery, fetchHistory } from "@/lib/api"
import { useNotifications } from "@/lib/NotificationsContext"
import type { AdmissionInfo } from "@/lib/admission"
import type { PatientDelivery, PatientHistoryEntry } from "@/lib/types"

interface HomeProps {
  bed: string
  admission: AdmissionInfo
  onResetBed: () => void
}

export function Home({ bed, admission, onResetBed }: HomeProps) {
  const [delivery, setDelivery] = useState<PatientDelivery | null>(null)
  const [history, setHistory] = useState<PatientHistoryEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [notifOpen, setNotifOpen] = useState(false)
  const [messageOpen, setMessageOpen] = useState(false)
  const [messageRefreshKey, setMessageRefreshKey] = useState(0)
  const [loadError, setLoadError] = useState("")
  const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null)
  const { unreadCount } = useNotifications()

  const reload = useCallback(async () => {
    setLoading(true)
    const [d, h] = await Promise.all([
      fetchCurrentDelivery(bed),
      fetchHistory(bed),
    ])
    const errors = [d.ok ? "" : d.error, h.ok ? "" : h.error].filter(Boolean)
    if (d.ok) setDelivery(d.data ?? null)
    if (h.ok) setHistory(h.data ?? [])
    setLoadError(errors.length ? errors.join("；") : "")
    setLastUpdatedAt(new Date())
    setLoading(false)
  }, [bed])

  useEffect(() => {
    void reload()
    // 后端接好后这里可以改成 SSE / WebSocket 推送, 现在用 5s 轮询占位
    const t = setInterval(reload, 5000)
    return () => clearInterval(t)
  }, [reload])

  return (
    <div className="min-h-screen flex flex-col">
      <AppHeader
        loading={loading}
        unreadCount={unreadCount}
        onRefresh={reload}
        onResetBed={onResetBed}
        onOpenNotifications={() => setNotifOpen(true)}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      <HeroCard
        bed={bed}
        wardName={delivery?.ward || admission.wardName}
        patientName={delivery?.patient_name || admission.patientName}
        age={delivery?.age}
        gender={delivery?.gender}
        heightCm={delivery?.height_cm}
        weightKg={delivery?.weight_kg}
      />

      <div className="app-shell px-3 pt-1">
        <div className={`rounded-2xl border px-4 py-3 text-sm leading-relaxed ${loadError ? "border-amber-200 bg-amber-50 text-amber-950" : "border-emerald-100 bg-white/70 text-slate-600"}`}>
          {loadError ? (
            <span>{"\u7f51\u7edc\u6216\u670d\u52a1\u6682\u65f6\u4e0d\u7a33\u5b9a\uff0c\u9875\u9762\u5df2\u4fdd\u7559\u6700\u8fd1\u4e00\u6b21\u6570\u636e\uff1a"}{loadError}</span>
          ) : (
            <span>{loading ? "\u6b63\u5728\u5237\u65b0\u6570\u636e..." : `\u6570\u636e\u5df2\u540c\u6b65${lastUpdatedAt ? ` · ${lastUpdatedAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : ""}`}</span>
          )}
        </div>
      </div>

      <main className="app-shell flex-1 px-3 pb-6 space-y-4 animate-fade-in">
        <RobotStatusCard bed={bed} />
        <HealthAlertCard delivery={delivery} />
        <ReportIssueCard
          bed={bed}
          delivery={delivery}
          onOpenMessage={() => setMessageOpen(true)}
        />
        {delivery ? (
          <DeliveryCard delivery={delivery} onUpdated={reload} />
        ) : (
          <EmptyOrder />
        )}

        <HistoryList entries={history} />
      </main>

      <div className="app-shell px-3">
        <ContactNurseButton
          bed={bed}
          deliveryId={delivery?.delivery_id}
          onClick={() => setMessageOpen(true)}
          refreshKey={messageRefreshKey}
          dialogOpen={messageOpen}
        />
      </div>

      <SettingsDialog
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        bed={bed}
        onResetBed={onResetBed}
      />
      <NotificationsDialog
        open={notifOpen}
        onOpenChange={setNotifOpen}
      />
      <MessageDialog
        open={messageOpen}
        onOpenChange={(v) => {
          setMessageOpen(v)
          if (!v) setMessageRefreshKey((k) => k + 1)
        }}
        bed={bed}
        deliveryId={delivery?.delivery_id}
      />
    </div>
  )
}
