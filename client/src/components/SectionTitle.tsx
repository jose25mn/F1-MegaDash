import { cn } from "@/lib/utils";

interface SectionTitleProps {
  title: string;
  className?: string;
}

export function SectionTitle({ title, className }: SectionTitleProps) {
  return (
    <h3 className={cn("text-xl font-bold text-white/80 mb-4 mt-8 uppercase tracking-wider border-b border-white/10 pb-2 inline-block", className)}>
      {title}
    </h3>
  );
}
