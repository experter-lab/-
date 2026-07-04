import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  ClipboardList,
  Clock,
  MapPin,
  Package,
  PackageCheck,
  Truck,
  XCircle,
  type LucideIcon,
} from "lucide-react"
import type { DeliveryStatus } from "./types"

export type BadgeVariant =
  | "default"
  | "secondary"
  | "success"
  | "warning"
  | "destructive"

export interface StatusMeta {
  text: string
  description: string
  badgeVariant: BadgeVariant
  icon: LucideIcon
  step: number
  isFinal: boolean
}

export const STATUS_META: Record<DeliveryStatus, StatusMeta> = {
  prescribed: {
    text: "已开方",
    description: "医生已下医嘱，药房正在准备。",
    badgeVariant: "secondary",
    icon: ClipboardList,
    step: 0,
    isFinal: false,
  },
  preparing: {
    text: "药房备药",
    description: "药房正在配药，机器人即将启程。",
    badgeVariant: "secondary",
    icon: Package,
    step: 1,
    isFinal: false,
  },
  dispatched: {
    text: "已出库",
    description: "机器人已携带药品离开药房。",
    badgeVariant: "default",
    icon: Truck,
    step: 2,
    isFinal: false,
  },
  delivering: {
    text: "配送中",
    description: "机器人正在前往您的床位。",
    badgeVariant: "default",
    icon: Truck,
    step: 2,
    isFinal: false,
  },
  arrived: {
    text: "已到达床旁",
    description: "机器人已到达，请核对后确认取药。",
    badgeVariant: "warning",
    icon: MapPin,
    step: 3,
    isFinal: false,
  },
  confirmed: {
    text: "已签收",
    description: "药品已交付，请按医嘱用药。",
    badgeVariant: "success",
    icon: PackageCheck,
    step: 3,
    isFinal: true,
  },
  rejected: {
    text: "已拒收",
    description: "工作人员将尽快与您联系。",
    badgeVariant: "destructive",
    icon: XCircle,
    step: 3,
    isFinal: true,
  },
  review: {
    text: "待护士复核",
    description: "已生成护士端复核提醒，请暂时不要服用，等待医护确认。",
    badgeVariant: "warning",
    icon: AlertTriangle,
    step: 3,
    isFinal: false,
  },
  cancelled: {
    text: "已取消",
    description: "本次配送已取消。",
    badgeVariant: "secondary",
    icon: Ban,
    step: 3,
    isFinal: true,
  },
  timeout: {
    text: "等待确认",
    description: "机器人已到位较久，系统已生成护士端提醒，您仍可核对后确认收药。",
    badgeVariant: "warning",
    icon: Clock,
    step: 3,
    isFinal: false,
  },
}

export interface ProgressStepDef {
  key: DeliveryStatus
  label: string
  icon: LucideIcon
}

export const PROGRESS_STEPS: ProgressStepDef[] = [
  { key: "prescribed", label: "开方", icon: ClipboardList },
  { key: "preparing", label: "药房备药", icon: Package },
  { key: "dispatched", label: "配送中", icon: Truck },
  { key: "arrived", label: "到达床旁", icon: CheckCircle2 },
]
