"use client"

import { useEffect, useState } from "react"
import { SentimentGauge } from "@/components/sentiment-gauge"
import { NewsFeed } from "@/components/news-feed"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { sentimentApi } from "@/lib/api"
import { useWebSocket } from "@/hooks/use-websocket"
import { useSession } from "next-auth/react"

export default function SentimentPage() {
  const { data: session, status }: any = useSession()
  const [globalSentiment, setGlobalSentiment] = useState({ score: 0, label: "Loading..." })
  const [aiSentiment, setAiSentiment] = useState({ score: 0, label: "Loading..." })

  const { lastMessage } = useWebSocket(process.env.NEXT_PUBLIC_WS_URL || null)

  useEffect(() => {
    const fetchSentiment = async () => {
      if (status !== "authenticated" || !session?.accessToken) return

      try {
        const data = await sentimentApi.getSentiment("BTCUSDT", session.accessToken)
        setAiSentiment({
          score: Math.round((data.score + 1) * 50), // Map -1..1 to 0..100
          label: data.sentiment || (data.score > 0.5 ? "Bullish" : data.score < -0.5 ? "Bearish" : "Neutral")
        })
      } catch (err) {
        console.error("Failed to fetch sentiment:", err)
      }
    }

    fetchSentiment()
  }, [session])

  useEffect(() => {
    if (lastMessage?.channel?.startsWith("sentiment:BTCUSDT")) {
      setAiSentiment({
        score: Math.round((lastMessage.score + 1) * 50),
        label: lastMessage.sentiment || (lastMessage.score > 0.5 ? "Bullish" : lastMessage.score < -0.5 ? "Bearish" : "Neutral")
      })
    }
  }, [lastMessage])

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Market Sentiment</h1>
          <p className="text-muted-foreground">Real-time analysis of news and social data</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Fear & Greed Index</CardTitle>
              <CardDescription>Overall market emotional state</CardDescription>
            </CardHeader>
            <CardContent className="relative">
              <SentimentGauge value={globalSentiment.score} label={globalSentiment.label} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>AI Sentiment (BTC)</CardTitle>
              <CardDescription>FinBERT analysis of latest news</CardDescription>
            </CardHeader>
            <CardContent>
               <SentimentGauge value={aiSentiment.score} label={aiSentiment.label} />
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-2">
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Live News Sentiment</CardTitle>
              <CardDescription>Latest headlines analyzed for market impact</CardDescription>
            </CardHeader>
            <CardContent>
              <NewsFeed />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
