"use client";

import { Check, ChevronDown } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { cn } from "../utils/cn";
import { toTitleCase } from "../utils/text";

export interface MultiSelectOption {
  id: string;
  nome: string;
}

export interface MultiSelectProps {
  options?: MultiSelectOption[];
  selectedIds?: string[];
  onChange?: (selectedIds: string[]) => void;
  labelAll?: string;
  className?: string;
  disabled?: boolean;
}

export function MultiSelect({
  options = [],
  selectedIds = [],
  onChange,
  labelAll = "Todas as entidades",
  className,
  disabled = false,
}: MultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const hasOptions = options.length > 0;
  const isAllSelected =
    selectedIds.length === 0 || selectedIds.length === options.length;

  const handleToggleAll = () => {
    onChange?.([]);
  };

  const handleToggleOption = (id: string) => {
    if (!onChange) return;
    if (selectedIds.length === 0) {
      const allExcept = options
        .map((opt) => opt.id)
        .filter((item) => item !== id);
      onChange(allExcept);
      return;
    }

    if (selectedIds.includes(id)) {
      const next = selectedIds.filter((item) => item !== id);
      onChange(next);
    } else {
      const next = [...selectedIds, id];
      if (next.length === options.length) {
        onChange([]);
      } else {
        onChange(next);
      }
    }
  };

  let displayText = labelAll;
  if (!hasOptions) {
    displayText = "Nenhuma entidade cadastrada";
  } else if (!isAllSelected && selectedIds.length > 0) {
    if (selectedIds.length === 1) {
      const found = options.find((o) => o.id === selectedIds[0]);
      displayText = found
        ? toTitleCase(found.nome)
        : `${selectedIds.length} selecionada`;
    } else {
      displayText = `${selectedIds.length} selecionadas`;
    }
  }

  const isBtnDisabled = disabled || !hasOptions;

  return (
    <div ref={containerRef} className={cn("relative w-full", className)}>
      <button
        type="button"
        disabled={isBtnDisabled}
        onClick={() => !isBtnDisabled && setIsOpen(!isOpen)}
        className={cn(
          "flex w-full items-center justify-between rounded-md border border-borderLine bg-white px-2.5 py-1.5 text-ink text-xs shadow-sm transition-colors",
          isBtnDisabled
            ? "cursor-not-allowed bg-gray-50 text-mutedText opacity-60"
            : "hover:border-gray-400 focus:border-[#1d64d8] focus:outline-none",
        )}
      >
        <span className="truncate pr-2 font-medium">{displayText}</span>
        <ChevronDown
          strokeWidth={1.6}
          className={cn(
            "h-3.5 w-3.5 shrink-0 text-mutedText transition-transform duration-200",
            isOpen && "rotate-180",
          )}
        />
      </button>

      {isOpen && hasOptions && (
        <div className="absolute z-50 mt-1 max-h-56 w-full overflow-auto rounded-md border border-borderLine bg-white py-1 text-xs shadow-lg">
          <button
            type="button"
            onClick={handleToggleAll}
            className="flex w-full cursor-pointer items-center gap-2 px-2.5 py-1.5 text-left font-medium text-ink hover:bg-gray-100/80"
          >
            <div
              className={cn(
                "flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded border border-borderLine transition-colors",
                isAllSelected
                  ? "border-[#1d64d8] bg-[#1d64d8] text-white"
                  : "bg-white",
              )}
            >
              {isAllSelected && (
                <Check strokeWidth={2.5} className="h-2.5 w-2.5" />
              )}
            </div>
            <span className="truncate">{labelAll}</span>
          </button>

          <div className="my-1 border-gray-100 border-t" />

          {options.map((opt) => {
            const isChecked = isAllSelected || selectedIds.includes(opt.id);
            return (
              <button
                type="button"
                key={opt.id}
                onClick={() => handleToggleOption(opt.id)}
                className="flex w-full cursor-pointer items-center gap-2 px-2.5 py-1.5 text-left text-ink hover:bg-gray-100/80"
              >
                <div
                  className={cn(
                    "flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded border border-borderLine transition-colors",
                    isChecked
                      ? "border-[#1d64d8] bg-[#1d64d8] text-white"
                      : "bg-white",
                  )}
                >
                  {isChecked && (
                    <Check strokeWidth={2.5} className="h-2.5 w-2.5" />
                  )}
                </div>
                <span className="truncate">{toTitleCase(opt.nome)}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
