"use client"

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Line,
  ComposedChart,
} from "recharts"

const data = [
  { risk: 10, return: 5 },
  { risk: 12, return: 8 },
  { risk: 15, return: 12 },
  { risk: 18, return: 15 },
  { risk: 22, return: 18 },
  { risk: 25, return: 20 },
  { risk: 30, return: 22 },
]

const currentPortfolio = [{ risk: 18, return: 15 }]

export function EfficientFrontierChart() {
  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart
          margin={{
            top: 20,
            right: 20,
            bottom: 20,
            left: 20,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
          <XAxis 
            type="number" 
            dataKey="risk" 
            name="Risk" 
            unit="%" 
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
          />
          <YAxis 
            type="number" 
            dataKey="return" 
            name="Return" 
            unit="%" 
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
          />
          <Tooltip 
             cursor={{ strokeDasharray: '3 3' }}
             contentStyle={{ 
                backgroundColor: "hsl(var(--background))", 
                borderColor: "hsl(var(--border))",
                borderRadius: "8px"
              }}
          />
          <Scatter 
            name="Efficient Frontier" 
            data={data} 
            fill="hsl(var(--primary))" 
            line={{ stroke: 'hsl(var(--primary))', strokeWidth: 2 }}
          />
          <Scatter 
            name="Your Portfolio" 
            data={currentPortfolio} 
            fill="#ef4444" 
            shape="star"
          />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  )
}
