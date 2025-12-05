import { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

interface DashboardCardProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
  className?: string;
  noPadding?: boolean;
}

export function DashboardCard({ title, subtitle, children, className, noPadding = false }: DashboardCardProps) {
  return (
    <Card className={cn("bg-card border-white/5 shadow-xl overflow-hidden flex flex-col h-full card-hover", className)}>
      <CardHeader className="pb-3 border-b border-white/5 bg-white/[0.02]">
        <CardTitle className="text-sm font-display font-bold tracking-wider text-white/90 uppercase flex items-center gap-2">
          <div className="w-1 h-4 bg-primary rounded-sm mr-1"></div>
          {title}
        </CardTitle>
        {subtitle && <CardDescription className="font-sans text-xs text-muted-foreground ml-4">{subtitle}</CardDescription>}
      </CardHeader>
      <CardContent className={cn("flex-1 min-h-0", noPadding ? "p-0" : "p-6")}>
        {children}
      </CardContent>
    </Card>
  );
}
