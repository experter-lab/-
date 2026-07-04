import React from "react"
import ReactDOM from "react-dom/client"
import App from "./App"
import "./index.css"
import { SettingsProvider } from "@/lib/SettingsContext"
import { NotificationsProvider } from "@/lib/NotificationsContext"

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <SettingsProvider>
      <NotificationsProvider>
        <App />
      </NotificationsProvider>
    </SettingsProvider>
  </React.StrictMode>,
)
