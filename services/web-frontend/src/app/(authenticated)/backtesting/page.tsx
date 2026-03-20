"use client"

import { useState } from "react"
import { useSession } from "next-auth/react"
import { EquityCurveChart } from "@/components/equity-curve-chart"
import { MetricsTable } from "@/components/metrics-table"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { backtestApi } from "@/lib/api"
import { Loader2, Play } from "lucide-react"

export default function BacktestingPage() {
  const { data: session } = useSession()
  const [ticker, setTicker] = useState("BTCUSDT")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleRunTest = async () => {
    setLoading(true)
    try {
      const data = await backtestApi.run(
        ticker.toUpperCase(), 
        "SMA_CROSSOVER", 
        10000, 
        (session as any)?.accessToken
      )
      setResult(data)
    } catch (err: any) {
      console.error("Backtest failed", err)
      alert(`Backtest failed: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const equityData = result?.equity_curve.map((item: any) => ({
    date: item.timestamp.split(" ")[0],
    balance: item.value
  }))

  const metricsData = result ? [
    { label: "Total Return", value: `${(result.total_return * 100).toFixed(1)}%`, highlight: result.total_return > 0 ? "text-green-500" : "text-red-500" },
    { label: "Sharpe Ratio", value: result.sharpe_ratio.toFixed(2), highlight: "text-primary" },
    { label: "Max Drawdown", value: `${(result.max_drawdown * 100).toFixed(1)}%`, highlight: "text-red-500" },
    { label: "Win Rate", value: `${(result.win_rate * 100).toFixed(0)}%`, highlight: "text-primary" },
  ] : []

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Strategy Backtesting</h1>
          <p className="text-muted-foreground">Analyze historical performance of your AI strategies</p>
        </div>
        <div className="flex gap-2 items-center">
            <Input 
                className="w-32" 
                value={ticker} 
                onChange={(e) => setTicker(e.target.value)} 
                placeholder="Ticker"
            />
            <Button onClick={handleRunTest} disabled={loading} className="gap-2">
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                Run Test
            </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Equity Curve</CardTitle>
            <CardDescription>
                {result ? `Historical performance of SMA Crossover on ${result.ticker}` : "Run a test to see results"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {result ? (
                <EquityCurveChart data={equityData} />
            ) : (
                <div className="h-[300px] flex items-center justify-center border-2 border-dashed rounded-lg bg-accent/5">
                    <p className="text-muted-foreground">No data yet. Enter a ticker and click Run Test.</p>
                </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Core Metrics</CardTitle>
            <CardDescription>Performance summary</CardDescription>
          </CardHeader>
          <CardContent>
            {result ? (
                <MetricsTable metrics={metricsData} />
            ) : (
                <p className="text-muted-foreground text-center py-10">Run a test to see metrics</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* History table could be added here if backend supports listing past runs */}
    </div>
  )
}
