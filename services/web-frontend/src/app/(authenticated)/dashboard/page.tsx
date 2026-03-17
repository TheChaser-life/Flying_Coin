"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useWebSocket } from "@/hooks/use-websocket"

export default function DashboardPage() {
  const [btcPrice, setBtcPrice] = useState(68432.12)
  const [ethPrice, setEthPrice] = useState(3842.50)
  
  // Real-world: const { lastMessage } = useWebSocket("wss://stream.binance.com:9443/ws/btcusdt@ticker")
  // For demo, we simulate the hook result
  useEffect(() => {
    const interval = setInterval(() => {
      setBtcPrice(prev => prev + (Math.random() - 0.5) * 10)
      setEthPrice(prev => prev + (Math.random() - 0.5) * 5)
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Market Overview</h1>
        <div className="flex items-center gap-2">
           <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
           <span className="text-sm font-medium text-muted-foreground">Live Market Data</span>
        </div>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">BTC/USDT</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${btcPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            <p className="text-xs text-green-500">+2.4% last 24h</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ETH/USDT</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${ethPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            <p className="text-xs text-red-500">-1.2% last 24h</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Volume</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">$1.2B</div>
            <p className="text-xs text-muted-foreground">+5% from yesterday</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Market Sentiment</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">Bullish</div>
            <p className="text-xs text-muted-foreground">Index: 72/100</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Market Activity</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px]">
             {/* Reusing a simplified version of ForecastChart or similar here would be good */}
             <div className="h-full flex items-center justify-center text-muted-foreground italic bg-accent/5 rounded-lg border-dashed border-2">
                Real-time chart stream active
             </div>
          </CardContent>
        </Card>
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Recent Predictions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center">
                <div className="ml-4 space-y-1">
                  <p className="text-sm font-medium leading-none">BTC Uptrend Predicted</p>
                  <p className="text-sm text-muted-foreground">Confidence: 85%</p>
                </div>
                <div className="ml-auto font-medium text-green-500">+4.2%</div>
              </div>
              <div className="flex items-center">
                <div className="ml-4 space-y-1">
                  <p className="text-sm font-medium leading-none">ETH Pivot Point</p>
                  <p className="text-sm text-muted-foreground">Confidence: 62%</p>
                </div>
                <div className="ml-auto font-medium text-yellow-500">Wait</div>
              </div>
              <div className="flex items-center">
                <div className="ml-4 space-y-1">
                  <p className="text-sm font-medium leading-none">SOL Momentum Shift</p>
                  <p className="text-sm text-muted-foreground">Confidence: 78%</p>
                </div>
                <div className="ml-auto font-medium text-green-500">+1.8%</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
