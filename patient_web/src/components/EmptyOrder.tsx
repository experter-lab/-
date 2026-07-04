import { Card, CardContent } from "@/components/ui/card"
import { RobotIllustration } from "@/components/RobotIllustration"
import { Phone, ScrollText } from "lucide-react"

export function EmptyOrder() {
  return (
    <Card className="relative overflow-hidden glass-panel">
      <CardContent className="relative flex flex-col items-center justify-center gap-4 py-10 text-center">
        <RobotIllustration
          className="h-24 w-24 text-primary/85"
          animate
        />
        <div>
          <div className="text-xl font-semibold">
            暂无进行中的药品配送
          </div>
          <div className="mt-1 text-base text-muted-foreground">
            医生开方后，药品配送会显示在这里。
          </div>
        </div>
        <div className="grid w-full gap-2 sm:grid-cols-2 mt-1">
          <div className="flex items-center gap-2 rounded-xl border border-border bg-secondary/60 px-3 py-3 text-left text-base">
            <Phone className="h-5 w-5 text-primary shrink-0" />
            <span className="text-muted-foreground">
              如需协助，请点击<span className="text-foreground font-medium">下方联系护士</span>
            </span>
          </div>
          <div className="flex items-center gap-2 rounded-xl border border-border bg-secondary/60 px-3 py-3 text-left text-base">
            <ScrollText className="h-5 w-5 text-primary shrink-0" />
            <span className="text-muted-foreground">
              历史用药记录可<span className="text-foreground font-medium">向下查看</span>
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
