export interface RibbonProps {
  cityName?: string;
}

export function Ribbon({ cityName }: RibbonProps) {
  return (
    <div className="flex items-center gap-2 border-[#dfe9f8] border-b bg-[#eef4fd] px-10 py-2.5 text-[#3a5a86] text-[11.5px]">
      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-[oklch(0.55_0.11_250)]" />
      <span>
        Iniciativa{" "}
        <strong className="font-semibold">livre e apartidária</strong>, sem
        vínculo com a administração municipal. Dados extraídos do Portal da
        Transparência oficial de {cityName}.
      </span>
    </div>
  );
}
