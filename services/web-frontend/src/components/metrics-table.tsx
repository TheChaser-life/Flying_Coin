interface Metric {
  label: string;
  value: string;
  highlight?: string;
}

export function MetricsTable({ metrics }: { metrics: Metric[] }) {

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
