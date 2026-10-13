import { useEffect, useRef, useState } from "react";
import type { Location, LocationInput } from "../../data/contract";
import { locate } from "../../data/intake";
import { apiMode } from "../../data/mode";
import { useLang, type Pair } from "../../i18n/lang";
import { S } from "../../i18n/strings";
import { LocationChip, locationSource } from "./LocationChip";
import { LocationMap } from "./LocationMap";

export function DeskLocation({ location, disabled, onApply }: { location?: Location; disabled: boolean; onApply: (input: LocationInput, location: Location) => void }) {
  const { t } = useLang();
  const [editing, setEditing] = useState(false);
  const searchOpen = location?.status !== "located" || editing;
  const [address, setAddress] = useState("");
  const [preview, setPreview] = useState<{ input: LocationInput; location: Location }>();
  const [used, setUsed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<Pair>();
  const request = useRef(0);
  useEffect(() => () => { request.current++; }, []);
  const find = async () => {
    const n = ++request.current;
    const input: LocationInput = { kind: "address", text: address.trim() };
    setBusy(true); setPreview(undefined); setUsed(false); setMessage(undefined);
    const result = await locate(input);
    if (n !== request.current) return;
    setBusy(false);
    if (!result.ok) { setMessage(apiMode() ? S.location.failed : S.common.needsServer); return; }
    setPreview({ input, location: result.value });
    if (result.value.status === "unlocated") setMessage(S.location.notFound);
    if (result.value.status === "outside_area") setMessage(S.location.outside);
  };
  return <section className="location-block" aria-labelledby="desk-location-title">
    <h3 id="desk-location-title">{t(S.location.title)}</h3>
    <div className="location-actions">
      <span className={`chip ${location?.status === "located" ? "chip-waiting" : "chip-unknown"}`}>{t(location ? S.location[location.status] : S.location.notGiven)}</span>
      <LocationChip location={location} viewer="desk" />
    </div>
    {location && <p className="fine-print">{t(location.precision ? S.location.precision[location.precision] : S.location.precision.unknown)} · {t(locationSource(location, "desk"))}</p>}
    {location?.status === "located" && location.at && <LocationMap at={location.at} zoneId={location.zoneId} segmentId={location.segmentId} />}
    {location?.status === "located" && <button type="button" className="btn btn-quiet" aria-expanded={searchOpen} aria-controls="desk-location-search" disabled={disabled || busy} onClick={() => setEditing(value => !value)}>{t(S.location.fixLocation)}</button>}
    <div id="desk-location-search" className="desk-location-search" hidden={!searchOpen}>
      <label htmlFor="desk-call-address">{t(S.location.callAddress)}</label>
      <div className="location-address">
        <input id="desk-call-address" value={address} disabled={busy || disabled} onChange={e => { setAddress(e.target.value); setPreview(undefined); setMessage(undefined); setUsed(false); }} onKeyDown={e => {
          if (e.key === "Enter") { e.preventDefault(); if (address.trim() && !busy && !disabled) void find(); }
        }} />
        <button type="button" className="btn btn-secondary" disabled={busy || disabled || !address.trim()} onClick={() => void find()}>{t(S.location.find)}</button>
      </div>
      <div role="status" aria-live="polite">
        {busy ? t(S.location.finding) : message && t(message)}
        {preview && <LocationChip location={preview.location} viewer="desk" />}
        {used && <p>{t(S.location.applied)}</p>}
      </div>
      {preview?.location.status === "located" && !used && <button type="button" className="btn btn-secondary" disabled={disabled} onClick={() => { onApply(preview.input, preview.location); setUsed(true); }}>{t(S.location.useLocation)}</button>}
    </div>
  </section>;
}
