import { ReactNode } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

interface DataTableProps<T> {
  columns: {
    header: string;
    accessorKey?: keyof T;
    cell?: (item: T) => ReactNode;
    className?: string;
  }[];
  data: T[];
  onRowClick?: (item: T) => void;
  className?: string;
  compact?: boolean;
}

export function DataTable<T>({ columns, data, onRowClick, className, compact = false }: DataTableProps<T>) {
  return (
    <div className={cn("w-full overflow-auto", className)}>
      <Table>
        <TableHeader className="bg-white/[0.02] sticky top-0 z-10 backdrop-blur-md">
          <TableRow className="hover:bg-transparent border-white/5">
            {columns.map((col, i) => (
              <TableHead 
                key={i} 
                className={cn(
                  "text-white/60 font-display text-xs uppercase tracking-wider font-bold",
                  compact ? "h-8 py-1" : "h-10",
                  col.className
                )}
              >
                {col.header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.length === 0 ? (
            <TableRow>
              <TableCell colSpan={columns.length} className="h-24 text-center text-muted-foreground">
                No results.
              </TableCell>
            </TableRow>
          ) : (
            data.map((row, rowIndex) => (
              <TableRow 
                key={rowIndex} 
                className={cn(
                  "border-white/5 transition-colors hover:bg-white/[0.04]",
                  onRowClick && "cursor-pointer active:bg-white/[0.08]",
                  rowIndex % 2 === 1 && "bg-white/[0.01]"
                )}
                onClick={() => onRowClick && onRowClick(row)}
              >
                {columns.map((col, colIndex) => (
                  <TableCell 
                    key={colIndex} 
                    className={cn(
                      "font-medium text-white/90",
                      compact ? "py-2" : "py-3",
                      col.className
                    )}
                  >
                    {col.cell ? col.cell(row) : (col.accessorKey ? (row[col.accessorKey] as ReactNode) : null)}
                  </TableCell>
                ))}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
