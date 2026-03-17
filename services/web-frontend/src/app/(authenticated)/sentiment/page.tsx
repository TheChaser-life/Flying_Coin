import { SentimentGauge } from "@/components/sentiment-gauge"
import { NewsFeed } from "@/components/news-feed"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"

export default function SentimentPage() {
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
              <CardTitle>Global Fear & Greed</CardTitle>
              <CardDescription>Current market emotional state</CardDescription>
            </CardHeader>
            <CardContent className="relative">
              <SentimentGauge value={72} label="Greed" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>AI Sentiment Score</CardTitle>
              <CardDescription>Aggregated news score (FinBERT)</CardDescription>
            </CardHeader>
            <CardContent>
               <SentimentGauge value={85} label="Bullish" />
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
