"use client"

import { useEffect, useState } from "react"
import { useSession } from "next-auth/react"
import { ForecastChart } from "@/components/forecast-chart"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { forecastApi, marketApi } from "@/lib/api"

export default function ForecastPage() {
  const { data: session }: any = useSession()
  const [forecastData, setForecastData] = useState<any>(null)
  const [marketHistory, setMarketHistory] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      if (!session?.accessToken) return
      
      try {
        setLoading(true)
        const [forecasts, history] = await Promise.all([
          forecastApi.getForecast("BTCUSDT", session.accessToken).catch(() => ({})),
          marketApi.getHistory("BTCUSDT", session.accessToken).catch(() => [])
        ])
        
        setForecastData(forecasts)
        setMarketHistory(history)
      } catch (error) {
        console.error("Failed to fetch forecast data:", error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
  }, [session])

  const lstmPrice = forecastData?.lstm?.predictions?.[0]
  const xgboostPrice = forecastData?.xgboost?.predictions?.[0]
  const arimaPrice = forecastData?.arima?.predictions?.[0]
  
  // Ensemble đơn giản: trung bình cộng của các model có sẵn
  const availablePrices = [lstmPrice, xgboostPrice, arimaPrice].filter(p => p !== undefined)
  const ensemblePrice = availablePrices.length > 0 
    ? availablePrices.reduce((a, b) => a + b, 0) / availablePrices.length 
    : null

  const formatPrice = (price: number | null) => 
    price ? `$${price.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : "N/A"

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Price Forecast</h1>
          <p className="text-muted-foreground">Multi-model price predictions for BTC/USDT</p>
        </div>
        <div className="flex items-center gap-2">
           <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20">
             Outlook: {ensemblePrice && marketHistory.length > 0 && ensemblePrice > marketHistory[marketHistory.length-1].close ? "Bullish" : "Neutral"}
           </Badge>
        </div>
      </div>

      <div className="grid gap-6">
        <Card className="col-span-1">
          <CardHeader>
            <CardTitle>Forecast Overview</CardTitle>
            <CardDescription>Comparing LSTM and XGBoost model predictions against actual market price</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="h-[400px] w-full flex items-center justify-center">Loading forecast data...</div>
            ) : (
              <ForecastChart marketData={marketHistory} forecastData={forecastData} />
            )}
          </CardContent>
        </Card>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
           <Card>
              <CardHeader>
                <CardTitle className="text-sm">LSTM Model</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatPrice(lstmPrice)}</div>
                <p className="text-xs text-muted-foreground">Predicted next price step</p>
                <div className="mt-4 text-sm text-green-500">Live AI Signal</div>
              </CardContent>
           </Card>
           <Card>
              <CardHeader>
                <CardTitle className="text-sm">XGBoost Model</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatPrice(xgboostPrice)}</div>
                <p className="text-xs text-muted-foreground">Predicted next price step</p>
                <div className="mt-4 text-sm text-green-500">Live ML Signal</div>
              </CardContent>
           </Card>
           <Card>
              <CardHeader>
                <CardTitle className="text-sm">Ensemble Result</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{formatPrice(ensemblePrice)}</div>
                <p className="text-xs text-muted-foreground">Weighted average prediction</p>
                <div className="mt-4 text-sm text-primary">High Accuracy Mode</div>
              </CardContent>
           </Card>
        </div>
      </div>
    </div>
  )
}
