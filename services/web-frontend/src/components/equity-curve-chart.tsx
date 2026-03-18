"use client"

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"

const data = [
  { date: "2024-01-01", balance: 10000 },
  { date: "2024-01-15", balance: 10500 },
  { date: "2024-02-01", balance: 10300 },
  { date: "2024-02-15", balance: 11200 },
  { date: "2024-03-01", balance: 12100 },
  { date: "2024-03-15", balance: 11800 },
  { date: "2024-04-01", balance: 13500 },
  { date: "2024-04-15", balance: 14200 },
]

export function EquityCurveChart() {
  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
          <XAxis 
            dataKey="date" 
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
            tickFormatter={(value) => value.split("-").slice(1).join("/")}
          />
          <YAxis 
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
            tickFormatter={(value) => `$${value/1000}k`}
          />
          <Tooltip 
             contentStyle={{ 
                backgroundColor: "hsl(var(--background))", 
                borderColor: "hsl(var(--border))",
                borderRadius: "8px"
              }}
          />
          <Area
            type="monotone"
            dataKey="balance"
            stroke="hsl(var(--primary))"
            fillOpacity={1}
            fill="url(#colorBalance)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
