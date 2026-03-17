import { ForecastChart } from "@/components/forecast-chart"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function ForecastPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Price Forecast</h1>
          <p className="text-muted-foreground">Multi-model price predictions for BTC/USDT</p>
        </div>
        <div className="flex items-center gap-2">
           <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20">
             7-Day Outlook: Bullish
           </Badge>
        </div>
      </div>

      <div className="grid gap-6">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Forecast Overview</CardTitle>
            <CardDescription>Comparing LSTM and Transformer model predictions against actual market price</CardDescription>
          </CardHeader>
          <CardContent>
            <ForecastChart />
          </CardContent>
        </Card>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
           <Card>
              <CardHeader>
                <CardTitle className="text-sm">LSTM Model</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">$70,500</div>
                <p className="text-xs text-muted-foreground">Predicted 5-day price</p>
                <div className="mt-4 text-sm text-green-500">+3.1% confidence</div>
              </CardContent>
           </Card>
           <Card>
              <CardHeader>
                <CardTitle className="text-sm">Transformer Model</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">$71,000</div>
                <p className="text-xs text-muted-foreground">Predicted 5-day price</p>
                <div className="mt-4 text-sm text-green-500">+3.8% confidence</div>
              </CardContent>
           </Card>
           <Card>
              <CardHeader>
                <CardTitle className="text-sm">Ensemble Result</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">$70,750</div>
                <p className="text-xs text-muted-foreground">Weighted average prediction</p>
                <div className="mt-4 text-sm text-primary">High Accuracy Mode</div>
              </CardContent>
           </Card>
        </div>
      </div>
    </div>
  )
}
