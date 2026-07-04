import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import path from "node:path"

// patient_web: 病人侧取药终端
// dev: 本地 5173 端口, 通过 /patient/api/* 代理到 board (8081)
// build: dist/ 静态文件由板子的 dashboard_node serve, 路径 /patient/ 下
export default defineConfig({
  plugins: [react()],
  base: "/patient/",
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      // 开发时把 API 请求转发到板子的 dashboard (假设板子 IP 是 192.168.31.125)
      "/patient/api": {
        target: "http://192.168.31.125:8081",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
    chunkSizeWarningLimit: 600,
  },
})
