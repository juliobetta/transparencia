import React from "react";
import { clsx } from "clsx";
import { AlertTriangle, Info, CheckCircle, AlertCircle } from "lucide-react";

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
    warning: <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />,
    danger: <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />,
    info: <Info className="w-5 h-5 text-blue-600 shrink-0" />,
    success: <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />,
  };

  const styles = {
    warning: "bg-amber-50/80 border-amber-200 text-amber-900",
    danger: "bg-rose-50/80 border-rose-200 text-rose-900",
    info: "bg-blue-50/80 border-blue-200 text-blue-900",
    success: "bg-emerald-50/80 border-emerald-200 text-emerald-900",
  };

  return (
    <div
      className={clsx(
        "flex gap-3 p-4 rounded-xl border text-sm leading-relaxed",
        styles[type],
        className
      )}
    >
      {icons[type]}
      <div>
        {title && <h4 className="font-semibold mb-1">{title}</h4>}
        <div>{children}</div>
      </div>
    </div>
  );
}
