import { Tr, useT } from "./lang";
export function DepthBars({ model, corrected, at }: {
  model: number | null; corrected: [number, number, number] | null; at?: string;
}) {
  const t = useT();
  const scale = Math.max(2, model ?? 0, corrected?.[2] ?? 0);
  const percent = (value: number) => `${Math.max(0, Math.min(100, value / scale * 100))}%`;
  return <div className="rp-depth-bars">
    {[[t("แบบจำลอง · Model", "Model"), model], [t("+ รายงาน · Reports", "Reports"), corrected?.[0] ?? null]].map(([label, value], index) =>
      <div key={index} className={`rp-depth-bar${index === 0 ? " is-model" : ""}`}>
        <span>{label}</span><span className="rp-depth-track">
          {typeof value === "number" && <i style={{ width: percent(value) }} />}
          {index === 1 && corrected && <u style={{ left: percent(corrected[1]), width: percent(corrected[2] - corrected[1]) }} />}
        </span><b>{typeof value === "number" ? `${value.toFixed(1)} m` : "?"}</b>
      </div>)}
    <p>{corrected ? t(`ช่วงประมาณ ${corrected[1].toFixed(1)}–${corrected[2].toFixed(1)} m · Likely range`, `Likely range ${corrected[1].toFixed(1)}–${corrected[2].toFixed(1)} m`) : t("ยังไม่ทราบระดับ · Depth unknown", "Depth unknown")}
      {at && <span> · {at}</span>}<small><Tr th="ค่าประมาณ ไม่ทราบไม่ได้แปลว่าแห้ง" en="Estimate; unknown is not dry." /></small></p>
  </div>;
}
