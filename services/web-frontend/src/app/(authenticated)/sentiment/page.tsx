"use client"

import { useEffect, useState } from "react"
import { NewsFeed, NewsItem } from "@/components/news-feed"
import { SentimentGauge } from "@/components/sentiment-gauge"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { sentimentApi } from "@/lib/api"
import { useWebSocket } from "@/hooks/use-websocket"
import { useSession } from "next-auth/react"
import { useThrottledState } from "@/hooks/use-throttled-state"

export default function SentimentPage() {
  const { data: session, status }: any = useSession()
  const [globalSentiment, setGlobalSentiment] = useThrottledState({ score: 0, label: "Loading..." }, 1000)
  const [aiSentiment, setAiSentiment] = useThrottledState({ score: 0, label: "Loading..." }, 1000)
  const [newsList, setNewsList] = useState<NewsItem[]>([])
  const [pendingNews, setPendingNews] = useState<NewsItem[]>([])
  const [isHoveringNews, setIsHoveringNews] = useState(false)

  const { lastMessage } = useWebSocket(process.env.NEXT_PUBLIC_WS_URL || null)

  const flushPendingNews = () => {
    if (pendingNews.length === 0) return
    setNewsList(prev => {
      const combined = [...pendingNews, ...prev]
      return combined.slice(0, 100)
    })
    setPendingNews([])
  }

  useEffect(() => {
    const fetchSentimentData = async () => {
      if (status !== "authenticated" || !session?.accessToken) return

      try {
        const simpleTicker = "BTC"
        const [btcData, generalData, btcHistory, generalHistory] = await Promise.all([
          sentimentApi.getSentiment(simpleTicker, session.accessToken).catch(err => {
            console.warn("Failed to fetch BTC sentiment:", err)
            return { sentiment_score: 0, sentiment_label: "Neutral" }
          }),
          sentimentApi.getSentiment("GENERAL", session.accessToken).catch(err => {
            console.warn("Failed to fetch general sentiment:", err)
            return { sentiment_score: 0, sentiment_label: "Neutral" }
          }),
          sentimentApi.getHistory(simpleTicker, session.accessToken).catch(err => {
            console.warn("Failed to fetch BTC history:", err)
            return []
          }),
          sentimentApi.getHistory("GENERAL", session.accessToken).catch(err => {
            console.warn("Failed to fetch general history:", err)
            return []
          })
        ])

        setAiSentiment({
          score: Math.round((btcData.sentiment_score + 1) * 50),
          label: btcData.sentiment_label || (btcData.sentiment_score > 0.5 ? "Bullish" : btcData.sentiment_score < -0.5 ? "Bearish" : "Neutral")
        })

        setGlobalSentiment({
          score: Math.round((generalData.sentiment_score + 1) * 50),
          label: generalData.sentiment_label || "Neutral"
        })

        // Gộp, lọc trùng lặp và tin cũ (>48h), sau đó sắp xếp
        const now = new Date().getTime()
        const fortyEightHoursAgo = now - (48 * 60 * 60 * 1000)

        const seenTitles = new Set()
        const combinedHistory = [...btcHistory, ...generalHistory]
          .filter(item => {
            const itemTs = new Date(item.timestamp).getTime()
            if (itemTs < fortyEightHoursAgo) return false
            if (seenTitles.has(item.title)) return false
            seenTitles.add(item.title)
            return true
          })
          .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
          .slice(0, 100)
        
        setNewsList(combinedHistory)
      } catch (err) {
        console.error("Failed to fetch sentiment:", err)
      }
    }

    fetchSentimentData()
  }, [session, status])

  useEffect(() => {
    if (!lastMessage) return

    const symbol = lastMessage?.symbol || lastMessage?.ticker || (lastMessage?.channel?.split(":")[1]);

    // Cập nhật chỉ số Gauge
    if (symbol === "BTC" || lastMessage?.channel?.startsWith("sentiment:BTC")) {
      setAiSentiment({
        score: Math.round(((lastMessage.sentiment_score || lastMessage.score) + 1) * 50),
        label: lastMessage.sentiment_label || lastMessage.sentiment || ((lastMessage.sentiment_score || lastMessage.score) > 0.5 ? "Bullish" : (lastMessage.sentiment_score || lastMessage.score) < -0.5 ? "Bearish" : "Neutral")
      })
    } else if (symbol === "GENERAL" || lastMessage?.channel?.startsWith("sentiment:GENERAL")) {
      setGlobalSentiment({
        score: Math.round(((lastMessage.sentiment_score || lastMessage.score) + 1) * 50),
        label: lastMessage.sentiment_label || lastMessage.sentiment || "Neutral"
      })
    }

    // Cập nhật News Feed nếu message chứa thông tin bài báo
    if (lastMessage.title && lastMessage.source) {
      let sanitizedUrl = (lastMessage.url || "").trim()
      if (sanitizedUrl.startsWith("web:")) {
        sanitizedUrl = sanitizedUrl.substring(4).trim()
      }

      const newItem: NewsItem = {
        title: lastMessage.title,
        source: lastMessage.source,
        timestamp: lastMessage.timestamp || new Date().toISOString(),
        sentiment_label: lastMessage.sentiment_label || "NEUTRAL",
        sentiment_score: lastMessage.latest_score || lastMessage.sentiment_score || 0,
        url: sanitizedUrl
      }

      // Kiểm tra xem tin này đã có trong danh sách hiển thị chưa (dựa trên tiêu đề)
      const isDuplicate = (list: NewsItem[]) => list.some(item => item.title === newItem.title)

      if (isHoveringNews) {
        setPendingNews(prev => {
          if (isDuplicate(prev) || newsList.some(item => item.title === newItem.title)) return prev
          const next = [newItem, ...prev]
          if (next.length >= 50) {
             setTimeout(flushPendingNews, 0)
          }
          return next
        })
      } else {
        setNewsList(prev => {
          if (isDuplicate(prev)) return prev
          return [newItem, ...prev].slice(0, 100)
        })
      }
    }
  }, [lastMessage, isHoveringNews])

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Market Sentiment</h1>
          <p className="text-muted-foreground">Rolling daily average of news and social data</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Global Sentiment</CardTitle>
              <CardDescription>Daily average emotional state</CardDescription>
            </CardHeader>
            <CardContent className="relative">
              <SentimentGauge value={globalSentiment.score} label={globalSentiment.label} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>AI Sentiment (BTC)</CardTitle>
              <CardDescription>Daily average of FinBERT analysis</CardDescription>
            </CardHeader>
            <CardContent>
               <SentimentGauge value={aiSentiment.score} label={aiSentiment.label} />
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-2">
          <Card className="h-full flex flex-col">
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div>
                <CardTitle>Live News Sentiment</CardTitle>
                <CardDescription>Latest headlines analyzed for market impact</CardDescription>
              </div>
              {pendingNews.length > 0 && (
                <button 
                  onClick={flushPendingNews}
                  className="bg-primary text-primary-foreground text-xs font-bold py-1 px-3 rounded-full animate-bounce hover:opacity-90 transition-opacity"
                >
                  {pendingNews.length} new articles
                </button>
              )}
              {isHoveringNews && pendingNews.length === 0 && (
                <span className="text-[10px] text-muted-foreground animate-pulse uppercase tracking-widest">
                  Paused for reading
                </span>
              )}
            </CardHeader>
            <CardContent className="flex-1 overflow-hidden">
              <NewsFeed 
                items={newsList} 
                onMouseEnter={() => setIsHoveringNews(true)}
                onMouseLeave={() => {
                  setIsHoveringNews(false)
                  flushPendingNews()
                }}
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
