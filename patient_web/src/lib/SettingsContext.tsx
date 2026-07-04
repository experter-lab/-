import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import {
  DEFAULT_SETTINGS,
  applyFontScale,
  loadSettings,
  saveSettings,
  type FontScale,
  type PatientSettings,
} from "@/lib/settings"

interface SettingsContextValue extends PatientSettings {
  setFontScale: (s: FontScale) => void
  setNotificationEnabled: (v: boolean) => void
  setElderlyModeEnabled: (v: boolean) => void
  setNurseAlertSoundEnabled: (v: boolean) => void
  setNurseBrowserNotificationEnabled: (v: boolean) => void
  setQuietHoursEnabled: (v: boolean) => void
  reset: () => void
}

const SettingsContext = createContext<SettingsContextValue | null>(null)

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<PatientSettings>(() => loadSettings())

  useEffect(() => {
    applyFontScale(state.fontScale)
  }, [state.fontScale])

  useEffect(() => {
    saveSettings(state)
  }, [state])

  const setFontScale = useCallback((s: FontScale) => {
    setState((cur) => ({ ...cur, fontScale: s }))
  }, [])

  const setNotificationEnabled = useCallback((v: boolean) => {
    setState((cur) => ({ ...cur, notificationEnabled: v }))
  }, [])

  const setElderlyModeEnabled = useCallback((v: boolean) => {
    setState((cur) => ({ ...cur, elderlyModeEnabled: v }))
  }, [])

  const setNurseAlertSoundEnabled = useCallback((v: boolean) => {
    setState((cur) => ({ ...cur, nurseAlertSoundEnabled: v }))
  }, [])

  const setNurseBrowserNotificationEnabled = useCallback((v: boolean) => {
    setState((cur) => ({ ...cur, nurseBrowserNotificationEnabled: v }))
  }, [])

  const setQuietHoursEnabled = useCallback((v: boolean) => {
    setState((cur) => ({ ...cur, quietHoursEnabled: v }))
  }, [])

  const reset = useCallback(() => {
    setState(DEFAULT_SETTINGS)
  }, [])

  const value = useMemo(
    () => ({
      ...state,
      setFontScale,
      setNotificationEnabled,
      setElderlyModeEnabled,
      setNurseAlertSoundEnabled,
      setNurseBrowserNotificationEnabled,
      setQuietHoursEnabled,
      reset,
    }),
    [
      state,
      setFontScale,
      setNotificationEnabled,
      setElderlyModeEnabled,
      setNurseAlertSoundEnabled,
      setNurseBrowserNotificationEnabled,
      setQuietHoursEnabled,
      reset,
    ],
  )

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  )
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext)
  if (!ctx) {
    throw new Error("useSettings must be used within SettingsProvider")
  }
  return ctx
}
