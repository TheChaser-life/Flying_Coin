"use client"

import { memo } from "react"
import { PieChart, Pie, Cell, ResponsiveContainer, Label } from "recharts"

export interface SentimentGaugeProps {
  value: number // 0 to 100
  label: string
}

export const SentimentGauge = memo(function SentimentGauge({ value, label }: SentimentGaugeProps) {
  const data = [
    { name: "score", value: value },
    { name: "remaining", value: 100 - value },
  ]

  const getColor = (v: number) => {
    if (v < 30) return "#ef4444" // red
    if (v < 70) return "#eab308" // yellow
    return "#22c55e" // green
  }

  return (
    <div className="h-[200px] w-full flex items-center justify-center">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="100%"
            startAngle={180}
            endAngle={0}
            innerRadius={60}
            outerRadius={80}
            paddingAngle={0}
            dataKey="value"
            stroke="none"
          >
            <Cell fill={getColor(value)} />
            <Cell fill="hsl(var(--muted))" />
            <Label
              value={`${value}`}
              position="centerBottom"
              className="fill-foreground font-bold text-3xl"
              dy={-20}
            />
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute mt-16 text-center">
        <p className="text-sm font-medium text-muted-foreground uppercase tracking-wider">{label}</p>
      </div>
    </div>
  )
})
