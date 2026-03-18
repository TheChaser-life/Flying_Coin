import TradingViewChart from "@/components/trading-view-chart"

export default function AnalysisPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Market Analysis</h1>
        <div className="flex gap-2">
            {/* Future: Timeframe selectors, symbols, etc. */}
        </div>
      </div>
      
      <div className="rounded-xl border bg-card text-card-foreground shadow overflow-hidden">
        <TradingViewChart />
      </div>
    </div>
  )
}
