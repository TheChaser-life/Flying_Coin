import { EquityCurveChart } from "@/components/equity-curve-chart"
import { MetricsTable } from "@/components/metrics-table"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function BacktestingPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Strategy Backtesting</h1>
          <p className="text-muted-foreground">Analyze historical performance of your AI strategies</p>
        </div>
        <Button>Run New Test</Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Equity Curve</CardTitle>
            <CardDescription>Historical performance of SMA Crossover Strategy</CardDescription>
          </CardHeader>
          <CardContent>
            <EquityCurveChart />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Core Metrics</CardTitle>
            <CardDescription>Performance summary</CardDescription>
          </CardHeader>
          <CardContent>
            <MetricsTable />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Test History</CardTitle>
          <CardDescription>Previous backtesting runs and their results</CardDescription>
        </CardHeader>
        <CardContent>
           <div className="relative overflow-x-auto">
             <table className="w-full text-sm text-left">
               <thead className="text-xs uppercase bg-accent/5">
                 <tr>
                   <th className="px-6 py-3">Strategy</th>
                   <th className="px-6 py-3">Period</th>
                   <th className="px-6 py-3">Return</th>
                   <th className="px-6 py-3">Status</th>
                 </tr>
               </thead>
               <tbody className="divide-y divide-border">
                  <tr>
                    <td className="px-6 py-4 font-medium">Mean Reversion</td>
                    <td className="px-6 py-4">Jan 24 - Mar 24</td>
                    <td className="px-6 py-4 text-green-500">+15.2%</td>
                    <td className="px-6 py-4">Completed</td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 font-medium">LSTM Trend</td>
                    <td className="px-6 py-4">Feb 24 - Mar 24</td>
                    <td className="px-6 py-4 text-red-500">-2.1%</td>
                    <td className="px-6 py-4">Completed</td>
                  </tr>
               </tbody>
             </table>
           </div>
        </CardContent>
      </Card>
    </div>
  )
}
