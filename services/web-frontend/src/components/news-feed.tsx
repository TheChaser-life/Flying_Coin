import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"

const newsItems = [
  {
    id: 1,
    title: "Bitcoin Surges Past $68k as Institutional Interest Peaks",
    source: "Coindesk",
    time: "2h ago",
    sentiment: "positive",
    score: 0.85,
  },
  {
    id: 2,
    title: "New Regulatory Framework Proposed for Stablecoins in EU",
    source: "Reuters",
    time: "4h ago",
    sentiment: "neutral",
    score: 0.12,
  },
  {
    id: 3,
    title: "Exchange Outage Sparks Temporary Price Dip in Major Altcoins",
    source: "CryptoPanic",
    time: "6h ago",
    sentiment: "negative",
    score: -0.65,
  },
  {
    id: 4,
    title: "Ethereum Layer 2 Adoption Hits All-Time High",
    source: "The Block",
    time: "8h ago",
    sentiment: "positive",
    score: 0.72,
  },
]

export function NewsFeed() {
  return (
    <div className="space-y-4">
      {newsItems.map((item) => (
        <Card key={item.id} className="overflow-hidden border-none bg-accent/5 hover:bg-accent/10 transition-colors">
          <CardContent className="p-4 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground font-mono uppercase italic">{item.source} • {item.time}</span>
              <Badge 
                variant="outline" 
                className={
                  item.sentiment === "positive" ? "bg-green-500/10 text-green-500 border-green-500/20" :
                  item.sentiment === "negative" ? "bg-red-500/10 text-red-500 border-red-500/20" :
                  "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"
                }
              >
                {item.sentiment}
              </Badge>
            </div>
            <h3 className="font-semibold leading-tight">{item.title}</h3>
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              Sentiment Score: <span className={item.sentiment === "positive" ? "text-green-500" : item.sentiment === "negative" ? "text-red-500" : "text-yellow-500"}>
                {item.score > 0 ? `+${item.score}` : item.score}
              </span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
