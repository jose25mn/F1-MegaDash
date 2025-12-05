import { cn } from "@/lib/utils";
import { Card, CardContent } from "@/components/ui/card";

interface KpiCardProps {
  label: string;
  value: string | number;
  hint?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  icon?: React.ReactNode;
  className?: string;
}

export function KpiCard({ label, value, hint, trend, trendValue, icon, className }: KpiCardProps) {
  return (
    <Card className={cn("bg-card border-white/5 shadow-lg relative overflow-hidden group", className)}>
      <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity scale-150 transform origin-top-right text-primary">
         {/* Optional background icon decoration */}
         {icon}
      </div>
      <CardContent className="p-6 relative z-10">
        <div className="flex flex-col gap-1">
          <span className="text-xs font-display font-bold tracking-wider text-muted-foreground uppercase">{label}</span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl md:text-4xl font-bold text-white tracking-tight">{value}</span>
            {trend && (
              <span className={cn(
                "text-xs font-bold px-1.5 py-0.5 rounded",
                trend === "up" ? "text-green-400 bg-green-400/10" : 
                trend === "down" ? "text-red-400 bg-red-400/10" : "text-gray-400"
              )}>
                {trend === "up" && "↑"} {trend === "down" && "↓"} {trendValue}
              </span>
            )}
          </div>
          {hint && <span className="text-xs text-white/40 mt-1">{hint}</span>}
        </div>
      </CardContent>
      {/* Bottom glow strip */}
      <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-primary/0 via-primary/50 to-primary/0 opacity-50"></div>
    </Card>
  );
}
