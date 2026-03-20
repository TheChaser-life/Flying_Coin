"use client"

import { useState } from "react"
import { useSession } from "next-auth/react"
import { AllocationChart } from "@/components/allocation-chart"
import { EfficientFrontierChart } from "@/components/efficient-frontier-chart"
import { MetricsTable } from "@/components/metrics-table"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { portfolioApi } from "@/lib/api"
import { Loader2, Plus, Zap } from "lucide-react"

export default function PortfolioPage() {
  const { data: session } = useSession()
  const [tickers, setTickers] = useState("BTC, ETH, SOL, USDT")
  const [risk, setRisk] = useState(0.5)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleOptimize = async () => {
    setLoading(true)
    try {
      const tickerList = tickers.split(",").map(t => t.trim().toUpperCase()).filter(t => t !== "")
      const data = await portfolioApi.optimize(tickerList, risk, (session as any)?.accessToken)
      setResult(data)
    } catch (err) {
      console.error("Optimization failed", err)
      alert("Failed to optimize portfolio. Please check your tickers and connection.")
    } finally {
      setLoading(false)
    }
  }

  const allocationData = result ? Object.entries(result.weights).map(([name, value], i) => ({
    name,
    value: (value as number) * 100,
    color: ["#f59e0b", "#6366f1", "#14b8a6", "#22c55e", "#ef4444", "#a855f7"][i % 6]
  })) : []

  const metricsData = result ? [
    { label: "Exp. Return", value: `${(result.expected_return * 100).toFixed(1)}%`, highlight: "text-green-500" },
    { label: "Volatility", value: `${(result.volatility * 100).toFixed(1)}%`, highlight: "text-primary" },
    { label: "Sharpe Ratio", value: result.sharpe_ratio.toFixed(2), highlight: "text-primary" },
  ] : []

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Portfolio Optimization</h1>
          <p className="text-muted-foreground">Manage and optimize your crypto assets with AI</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-1">
          <CardHeader>
            <CardTitle>Settings</CardTitle>
            <CardDescription>Adjust your preference</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Assets (Tickers)</label>
              <Input 
                value={tickers} 
                onChange={(e) => setTickers(e.target.value)}
                placeholder="BTC, ETH, SOL..."
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Risk Tolerance: {(risk * 10).toFixed(0)}</label>
              <input 
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={risk}
                onChange={(e) => setRisk(parseFloat(e.target.value))}
                className="w-full h-2 bg-accent rounded-lg appearance-none cursor-pointer accent-primary"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Safe</span>
                <span>Aggressive</span>
              </div>
            </div>
            <Button className="w-full gap-2" onClick={handleOptimize} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
              Optimize Portfolio
            </Button>
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Asset Allocation</CardTitle>
            <CardDescription>Target distribution for optimal performance</CardDescription>
          </CardHeader>
          <CardContent>
            {result ? (
              <div className="grid md:grid-cols-2 gap-4 items-center">
                <AllocationChart data={allocationData} />
                <MetricsTable metrics={metricsData} />
              </div>
            ) : (
              <div className="h-[300px] flex flex-col items-center justify-center text-center space-y-2 border-2 border-dashed rounded-lg bg-accent/5">
                 <p className="text-muted-foreground">No data yet. Configure your assets and click Optimize.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Efficient Frontier</CardTitle>
            <CardDescription>Risk vs Return visualization</CardDescription>
          </CardHeader>
          <CardContent>
            <EfficientFrontierChart />
          </CardContent>
        </Card>

        {result && (
          <Card>
            <CardHeader>
              <CardTitle>AI Insights</CardTitle>
              <CardDescription>Strategy recommendations</CardDescription>
            </CardHeader>
            <CardContent>
               <div className="space-y-4">
                  {Object.entries(result.weights).filter(([_, w]) => (w as number) > 0.05).map(([name, weight]) => (
                    <div key={name} className="flex items-center justify-between p-4 rounded-lg bg-accent/5">
                        <div>
                          <p className="font-medium">Increase {name} exposure</p>
                          <p className="text-sm text-muted-foreground">Recommended target: {((weight as number) * 100).toFixed(1)}%</p>
                        </div>
                        <div className="text-green-500 font-bold">Buy</div>
                    </div>
                  ))}
               </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
