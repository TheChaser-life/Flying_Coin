import { memo } from "react"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"

export interface NewsItem {
  id?: string | number
  title: string
  source: string
  timestamp: string
  sentiment_label: string
  sentiment_score: number
  url?: string
}

interface NewsFeedProps {
  items: NewsItem[]
  onMouseEnter?: () => void
  onMouseLeave?: () => void
}

export const NewsFeed = memo(function NewsFeed({ items, onMouseEnter, onMouseLeave }: NewsFeedProps) {
  if (!items || items.length === 0) {
    return (
      <div 
        className="flex flex-col items-center justify-center py-12 text-muted-foreground italic"
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
      >
        No news items yet. Monitoring feeds...
      </div>
    )
  }

  return (
    <div 
      className="space-y-4 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      {items.map((item, index) => (
        <Card key={item.id || index} className="overflow-hidden border-none bg-accent/5 hover:bg-accent/10 transition-colors">
          <CardContent className="p-4 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground font-mono uppercase italic">
                {item.source} • {new Date(item.timestamp).toLocaleString()}
              </span>
              <Badge 
                variant="outline" 
                className={
                  item.sentiment_label === "POSITIVE" ? "bg-green-500/10 text-green-500 border-green-500/20" :
                  item.sentiment_label === "NEGATIVE" ? "bg-red-500/10 text-red-500 border-red-500/20" :
                  "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"
                }
              >
                {item.sentiment_label}
              </Badge>
            </div>
            {item.url ? (
              <a href={item.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                <h3 className="font-semibold leading-tight">{item.title}</h3>
              </a>
            ) : (
              <h3 className="font-semibold leading-tight">{item.title}</h3>
            )}
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              Sentiment Score: <span className={item.sentiment_label === "POSITIVE" ? "text-green-500" : item.sentiment_label === "NEGATIVE" ? "text-red-500" : "text-yellow-500"}>
                {item.sentiment_score > 0 ? `+${item.sentiment_score.toFixed(4)}` : item.sentiment_score.toFixed(4)}
              </span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
})
