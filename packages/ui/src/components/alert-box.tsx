import { AlertCircle, AlertTriangle, CheckCircle, Info } from "lucide-react";
import type React from "react";
import { cn } from "../utils/cn";

export interface AlertBoxProps {
  type?: "warning" | "danger" | "info" | "success";
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function AlertBox({
  type = "warning",
  title,
  children,
  className,
}: AlertBoxProps) {
  const icons = {
    warning: <AlertTriangle className="h-5 w-5 shrink-0 text-amber-600" />,
    danger: <AlertCircle className="h-5 w-5 shrink-0 text-rose-600" />,
    info: <Info className="h-5 w-5 shrink-0 text-blue-600" />,
    success: <CheckCircle className="h-5 w-5 shrink-0 text-emerald-600" />,
  };

  const styles = {
    warning: "bg-amber-50/80 border-amber-200 text-amber-900",
    danger: "bg-rose-50/80 border-rose-200 text-rose-900",
    info: "bg-blue-50/80 border-blue-200 text-blue-900",
    success: "bg-emerald-50/80 border-emerald-200 text-emerald-900",
  };

  return (
    <div
      className={cn(
        "flex gap-3 rounded-xl border p-4 text-sm leading-relaxed",
        styles[type],
        className,
      )}
    >
      {icons[type]}
      <div>
        {title && <h4 className="mb-1 font-semibold">{title}</h4>}
        <div>{children}</div>
      </div>
    </div>
  );
}
