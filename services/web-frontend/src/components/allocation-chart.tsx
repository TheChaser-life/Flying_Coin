"use client"

import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts"

const data = [
  { name: "BTC", value: 45, color: "#f59e0b" },
  { name: "ETH", value: 30, color: "#6366f1" },
  { name: "SOL", value: 15, color: "#14b8a6" },
  { name: "USDT", value: 10, color: "#22c55e" },
]

export function AllocationChart() {
  return (
    <div className="h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={5}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{ 
              backgroundColor: "hsl(var(--background))", 
              borderColor: "hsl(var(--border))",
              borderRadius: "8px"
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
