import { useEffect, useRef, useState } from "react";
import type { Location, LocationInput } from "../../data/contract";
import { locate } from "../../data/intake";
import { deviceLocation } from "../../data/deviceLocation";
import { apiMode } from "../../data/mode";
import { useLang, type Pair } from "../../i18n/lang";
import { S } from "../../i18n/strings";
import { Icon } from "../../ui/Icon";
import { LocationChip } from "./LocationChip";
import { LocationMap } from "./LocationMap";

export function CallerLocation({ onChange, onBusy }: { onChange: (input?: LocationInput) => void; onBusy: (busy: boolean) => void }) {
  const { t } = useLang();
  const [address, setAddress] = useState("");
  const [resolved, setResolved] = useState<Location>();
  const [map, setMap] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<Pair>();
  const generation = useRef(0);
  useEffect(() => () => { generation.current++; }, []);
  const working = (value: boolean) => { setBusy(value); onBusy(value); };
  const clear = () => { generation.current++; working(false); setResolved(undefined); setMessage(undefined); onChange(undefined); };
  const preview = async (input: LocationInput, request = ++generation.current) => {
    working(true);
    setMessage(undefined);
    const result = await locate(input);
    if (request !== generation.current) return;
    working(false);
    if (!result.ok) { setMessage(apiMode() ? S.location.failed : S.common.needsServer); return; }
    // Keep even an unresolved address: the desk can still locate it by hand (D25).
    setResolved(result.value);
    onChange(input);
    setMap(false);
    if (result.value.status === "unlocated") setMessage(S.location.notFound);
    if (result.value.status === "outside_area") { setMessage(S.location.outside); setMap(true); }
  };
  const gps = async () => {
    const request = ++generation.current;
    working(true);
    setMessage(undefined);
    // In fixtures, never request device permission or send a coordinate.
    if (!apiMode()) { working(false); setMessage(S.common.needsServer); return; }
    const result = await deviceLocation();
    if (request !== generation.current) return;
    if (!result.ok) { working(false); setMessage(S.location[result.reason]); setMap(true); return; }
    await preview(result.input, request);
  };
  return <section className="location-block" aria-labelledby="caller-location-title">
    <h2 id="caller-location-title">{t(S.location.where)}</h2>
    <p className="fine-print">{t(S.location.optional)}</p>
    {resolved && <div className="location-actions"><LocationChip location={resolved} /><button type="button" className="btn btn-secondary" onClick={clear}>{t(S.location.change)}</button></div>}
    {!resolved && <>
      <div className="location-actions">
        <button type="button" className="btn btn-secondary" disabled={busy} onClick={() => void gps()}><Icon name="pin" />{t(S.location.gps)}</button>
        <button type="button" className="btn btn-secondary" disabled={busy} onClick={() => setMap(true)}><Icon name="map" />{t(S.location.map)}</button>
      </div>
      <label htmlFor="caller-address">{t(S.location.address)}</label>
      <div className="location-address">
        <input id="caller-address" value={address} disabled={busy} onChange={e => setAddress(e.target.value)} onKeyDown={e => {
          if (e.key === "Enter") { e.preventDefault(); if (address.trim() && !busy) void preview({ kind: "address", text: address.trim() }); }
        }} />
        <button type="button" className="btn btn-secondary" disabled={busy || !address.trim()} onClick={() => void preview({ kind: "address", text: address.trim() })}>{t(S.location.find)}</button>
      </div>
    </>}
    <div role="status" aria-live="polite">{busy ? t(S.location.finding) : message && t(message)}</div>
    {resolved && resolved.status !== "located" && !map && <button type="button" className="btn btn-secondary" disabled={busy} onClick={() => setMap(true)}>{t(S.location.map)}</button>}
    {map && !busy && <LocationMap onConfirm={at => void preview({ kind: "pin", lon: at[0], lat: at[1], method: "map" })} />}
    {(map || busy) && <button type="button" className="btn btn-secondary" onClick={() => { generation.current++; working(false); setMap(false); }}>{t(S.location.cancel)}</button>}
    <p className="fine-print"><Icon name="lock" size={16} /> {t(S.location.privacy)}</p>
  </section>;
}
