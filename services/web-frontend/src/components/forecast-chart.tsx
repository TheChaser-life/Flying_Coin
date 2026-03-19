"use client"

import {
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

interface ForecastChartProps {
  marketData: any[]
  forecastData: any
}

export function ForecastChart({ marketData, forecastData }: ForecastChartProps) {
  // Sắp xếp dữ liệu theo thời gian tăng dần
  const sortedMarketData = [...marketData].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  )

  // Chuẩn bị dữ liệu cho biểu đồ
  // Gộp lịch sử thị trường (20 điểm cuối cùng)
  const chartData = sortedMarketData.slice(-20).map(item => ({
    name: new Date(item.timestamp).toLocaleDateString(undefined, { 
      day: 'numeric', 
      month: 'numeric' 
    }),
    actual: item.close,
    timestamp: new Date(item.timestamp).getTime(),
    fullDate: new Date(item.timestamp).toLocaleDateString()
  }))

  // Thêm các điểm dự báo
  if (forecastData && chartData.length > 0) {
    const lastTimestamp = chartData[chartData.length - 1].timestamp
    const msPerDay = 24 * 60 * 60 * 1000
    
    // Giả sử các model có cùng horizon và interval (1 ngày)
    // Lấy predictions từ các model (arima, xgboost, lstm)
    const models = ["arima", "xgboost", "lstm"]
    const predsMap: Record<string, number[]> = {}
    
    let maxHorizon = 0
    models.forEach(m => {
      const preds = forecastData[m]?.predictions || []
      predsMap[m] = preds
      maxHorizon = Math.max(maxHorizon, preds.length)
    })
    
    for (let i = 0; i < maxHorizon; i++) {
      const forecastDate = new Date(lastTimestamp + (i + 1) * msPerDay)
      chartData.push({
        name: forecastDate.toLocaleDateString(undefined, { 
          day: 'numeric', 
          month: 'numeric' 
        }),
        lstm: predsMap.lstm[i],
        xgboost: predsMap.xgboost[i],
        arima: predsMap.arima[i],
        forecast: true,
        timestamp: forecastDate.getTime(),
        fullDate: forecastDate.toLocaleDateString()
      } as any)
    }
  }

  return (
    <div className="h-[400px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={chartData}
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
            tickFormatter={(value, index) => {
               // Chỉ hiển thị vài nhãn để tránh chật chội
               return index % (Math.ceil(chartData.length / 8)) === 0 ? value : ""
            }}
            axisLine={false}
          />
          <YAxis 
            stroke="hsl(var(--muted-foreground))" 
            fontSize={12}
            tickLine={false}
            axisLine={false}
            domain={['auto', 'auto']}
            tickFormatter={(value) => `$${Math.round(value / 1000)}k`}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: "hsl(var(--background))", 
              borderColor: "hsl(var(--border))",
              borderRadius: "8px"
            }}
            itemStyle={{ fontSize: "12px" }}
            labelFormatter={(label, payload) => {
               if (payload && payload[0]) {
                 return new Date(payload[0].payload.timestamp).toLocaleDateString()
               }
               return label
            }}
          />
          <Legend verticalAlign="top" height={36}/>
          <Area
            type="monotone"
            dataKey="actual"
            stroke="hsl(var(--primary))"
            fillOpacity={1}
            fill="url(#colorActual)"
            strokeWidth={2}
            dot={{ r: 2 }}
            activeDot={{ r: 4 }}
            name="Actual Price"
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="lstm"
            stroke="#8884d8"
            strokeWidth={2}
            strokeDasharray="5 5"
            name="LSTM Prediction"
            dot={false}
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="xgboost"
            stroke="#82ca9d"
            strokeWidth={2}
            strokeDasharray="5 5"
            name="XGBoost"
            dot={false}
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="arima"
            stroke="#ffc658"
            strokeWidth={2}
            strokeDasharray="5 5"
            name="ARIMA"
            dot={false}
            connectNulls
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
