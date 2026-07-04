// Patient preference settings: font scale + reminder strategy.
// Keep this file ASCII-only. UI Chinese strings use JS unicode escapes.

export type FontScale = "small" | "medium" | "large" | "xlarge"

export const FONT_SCALE_PX: Record<FontScale, number> = {
  small: 15,
  medium: 17,
  large: 19,
  xlarge: 22,
}

export const FONT_SCALE_LABEL: Record<FontScale, string> = {
  small: "\u6807\u51c6",
  medium: "\u9002\u4e2d",
  large: "\u8f83\u5927",
  xlarge: "\u7279\u5927",
}

export interface PatientSettings {
  fontScale: FontScale
  notificationEnabled: boolean
  elderlyModeEnabled: boolean
  nurseAlertSoundEnabled: boolean
  nurseBrowserNotificationEnabled: boolean
  quietHoursEnabled: boolean
}

export const DEFAULT_SETTINGS: PatientSettings = {
  fontScale: "medium",
  notificationEnabled: true,
  elderlyModeEnabled: false,
  nurseAlertSoundEnabled: true,
  nurseBrowserNotificationEnabled: true,
  quietHoursEnabled: false,
}

const STORAGE_KEY = "patient_web.settings"

export function loadSettings(): PatientSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return DEFAULT_SETTINGS
    const parsed = JSON.parse(raw) as Partial<PatientSettings>
    return { ...DEFAULT_SETTINGS, ...parsed }
  } catch {
    return DEFAULT_SETTINGS
  }
}

export function saveSettings(s: PatientSettings) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(s))
  } catch {
    // ignore
  }
}

export function applyFontScale(scale: FontScale) {
  document.documentElement.style.fontSize = `${FONT_SCALE_PX[scale]}px`
}

export function isQuietHoursActive(now = new Date()) {
  const hour = now.getHours()
  return hour >= 21 || hour < 7
}
