import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  className?: string;
}

export function PageHeader({ title, subtitle, className }: PageHeaderProps) {
  return (
    <div className={cn("mb-8", className)}>
      <h1 className="text-3xl md:text-4xl font-black text-white mb-2 tracking-tight uppercase drop-shadow-lg">
        {title}
      </h1>
      {subtitle && (
        <p className="text-lg text-muted-foreground font-medium max-w-3xl border-l-2 border-primary/50 pl-4">
          {subtitle}
        </p>
      )}
    </div>
  );
}
