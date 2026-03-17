"use client"

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts"

const data = [
  { name: "Mon", actual: 65000, lstm: 65200, transformer: 64800 },
  { name: "Tue", actual: 66200, lstm: 66000, transformer: 66500 },
  { name: "Wed", actual: 65800, lstm: 66100, transformer: 65900 },
  { name: "Thu", actual: 67100, lstm: 67000, transformer: 67300 },
  { name: "Fri", actual: 68400, lstm: 68200, transformer: 68600 },
  { name: "Sat", forecast: true, lstm: 69100, transformer: 69500 },
  { name: "Sun", forecast: true, lstm: 69800, transformer: 70200 },
  { name: "Mon", forecast: true, lstm: 70500, transformer: 71000 },
]

export function ForecastChart() {
  return (
    <div className="h-[400px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{
            top: 10,
            right: 30,
            left: 0,
            bottom: 0,
          }}
        >
          <defs>
            <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--muted-foreground))" opacity={0.1} />
          <XAxis 
            dataKey="name" 
            stroke="hsl(var(--muted-foreground))" 
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis 
            stroke="hsl(var(--muted-foreground))" 
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `$${value / 1000}k`}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: "hsl(var(--background))", 
              borderColor: "hsl(var(--border))",
              borderRadius: "8px"
            }}
            itemStyle={{ fontSize: "12px" }}
          />
          <Legend verticalAlign="top" height={36}/>
          <Area
            type="monotone"
            dataKey="actual"
            stroke="hsl(var(--primary))"
            fillOpacity={1}
            fill="url(#colorActual)"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
            name="Actual Price"
          />
          <Line
            type="monotone"
            dataKey="lstm"
            stroke="#8884d8"
            strokeWidth={2}
            strokeDasharray="5 5"
            name="LSTM Prediction"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="transformer"
            stroke="#82ca9d"
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Transformer"
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
