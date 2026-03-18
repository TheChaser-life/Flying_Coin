export function MetricsTable() {
  const metrics = [
    { label: "Total Return", value: "+42.5%", highlight: "text-green-500" },
    { label: "Sharpe Ratio", value: "2.1", highlight: "text-primary" },
    { label: "Max Drawdown", value: "-12.3%", highlight: "text-red-500" },
    { label: "Win Rate", value: "68%", highlight: "text-primary" },
    { label: "Total Trades", value: "142", highlight: "text-muted-foreground" },
    { label: "Avg. Profit/Trade", value: "$45.2", highlight: "text-green-500" },
  ]

  return (
    <div className="grid grid-cols-2 gap-4">
      {metrics.map((m) => (
        <div key={m.label} className="flex flex-col p-4 rounded-lg bg-accent/5 border">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">{m.label}</span>
          <span className={`text-xl font-bold ${m.highlight}`}>{m.value}</span>
        </div>
      ))}
    </div>
  )
}
