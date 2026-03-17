import { AllocationChart } from "@/components/allocation-chart"
import { EfficientFrontierChart } from "@/components/efficient-frontier-chart"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"

export default function PortfolioPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Portfolio Optimization</h1>
          <p className="text-muted-foreground">Manage and optimize your crypto assets</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Asset Allocation</CardTitle>
            <CardDescription>Current distribution across major assets</CardDescription>
          </CardHeader>
          <CardContent>
            <AllocationChart />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Efficient Frontier</CardTitle>
            <CardDescription>Risk vs Return optimization visualization</CardDescription>
          </CardHeader>
          <CardContent>
            <EfficientFrontierChart />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Optimization Strategy</CardTitle>
          <CardDescription>AI-driven portfolio rebalancing suggestions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
             <div className="flex items-center justify-between p-4 rounded-lg bg-accent/5">
                <div>
                   <p className="font-medium">Increase SOL exposure</p>
                   <p className="text-sm text-muted-foreground">Diversification benefit: High</p>
                </div>
                <div className="text-green-500 font-bold">+5%</div>
             </div>
             <div className="flex items-center justify-between p-4 rounded-lg bg-accent/5">
                <div>
                   <p className="font-medium">Hedge with USDT</p>
                   <p className="text-sm text-muted-foreground">Current volatility: Elevated</p>
                </div>
                <div className="text-primary font-bold">Recommended</div>
             </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
