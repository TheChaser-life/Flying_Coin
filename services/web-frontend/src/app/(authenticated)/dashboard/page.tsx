"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useWebSocket } from "@/hooks/use-websocket"
import { marketApi, sentimentApi } from "@/lib/api"
import TradingViewChart from "@/components/trading-view-chart"
import { useSession } from "next-auth/react"

export default function DashboardPage() {
  const { data: session, status }: any = useSession()
  const [btcPrice, setBtcPrice] = useState(0)
  const [ethPrice, setEthPrice] = useState(0)
  const [sentiment, setSentiment] = useState({ score: 0, label: "Loading..." })
  
  const { lastMessage } = useWebSocket(process.env.NEXT_PUBLIC_WS_URL || null)

  useEffect(() => {
    // Initial fetch for latest data
    const fetchInitialData = async () => {
      if (status !== "authenticated" || !session?.accessToken) return

      // Helper to map tickers for sentiment API
      const getSentimentTicker = (ticker: string) => ticker.replace("USDT", "")

      // Fetch prices
      try {
        const btcData = await marketApi.getLatestPrice("BTCUSDT", session.accessToken)
        setBtcPrice(btcData.close)
      } catch (err) {
        console.error("Failed to fetch BTC price:", err)
      }

      try {
        const ethData = await marketApi.getLatestPrice("ETHUSDT", session.accessToken)
        setEthPrice(ethData.close)
      } catch (err) {
        console.error("Failed to fetch ETH price:", err)
      }

      // Fetch sentiment
      try {
        const btcSentimentTicker = getSentimentTicker("BTCUSDT")
        const sentData = await sentimentApi.getSentiment(btcSentimentTicker, session.accessToken)
        
        setSentiment({ 
            score: sentData.sentiment_score, 
            label: sentData.sentiment_score > 0.5 ? "Bullish" : sentData.sentiment_score < -0.5 ? "Bearish" : "Neutral" 
        })
      } catch (err) {
        console.error("Failed to fetch initial sentiment data:", err)
        setSentiment({ score: 0, label: "Neutral" })
      }
    }

    fetchInitialData()
  }, [session, status])

  // Handle WebSocket updates
  useEffect(() => {
    if (lastMessage) {
      const ticker = lastMessage.ticker || lastMessage.symbol || (lastMessage.channel?.split(":")[1]);
      
      if (ticker === "BTCUSDT" || lastMessage.channel === "price:BTCUSDT") {
        setBtcPrice(lastMessage.close || lastMessage.price)
      } else if (ticker === "ETHUSDT" || lastMessage.channel === "price:ETHUSDT") {
        setEthPrice(lastMessage.close || lastMessage.price)
      } else if (ticker === "BTC" || lastMessage.channel?.startsWith("sentiment:BTC")) {
        setSentiment({
            score: lastMessage.sentiment_score || lastMessage.score,
            label: (lastMessage.sentiment_score || lastMessage.score) > 0.5 ? "Bullish" : (lastMessage.sentiment_score || lastMessage.score) < -0.5 ? "Bearish" : "Neutral"
        })
      }
    }
  }, [lastMessage])

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
            <div className="text-2xl font-bold">
                {btcPrice > 0 ? `$${btcPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "Loading..."}
            </div>
            <p className="text-xs text-green-500">+Real-time</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ETH/USDT</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
                {ethPrice > 0 ? `$${ethPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "Loading..."}
            </div>
            <p className="text-xs text-red-500">+Real-time</p>
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
            <div className={`text-2xl font-bold ${sentiment.score > 0 ? 'text-green-500' : 'text-red-500'}`}>
                {sentiment.label}
            </div>
            <p className="text-xs text-muted-foreground">Score: {sentiment.score.toFixed(2)}</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Market Activity</CardTitle>
          </CardHeader>
          <CardContent className="h-[600px] p-0 overflow-hidden">
             <TradingViewChart />
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
