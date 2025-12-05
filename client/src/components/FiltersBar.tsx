import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface FiltersBarProps {
  children: ReactNode;
  className?: string;
}

export function FiltersBar({ children, className }: FiltersBarProps) {
  return (
    <div
      className={cn(
        "flex flex-col md:flex-row flex-wrap items-start md:items-center gap-4 mb-6 p-4 bg-white/[0.03] rounded-lg border border-white/5 backdrop-blur-sm",
        className,
      )}
    >
      {children}
    </div>
  );
}
