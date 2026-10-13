import { useEffect, useRef, useState } from "react";
import { loadGoogleMaps, type Maps } from "../../data/googleMaps";
import { demoBounds } from "../../data/locationMap";
import { useLang } from "../../i18n/lang";
import { S } from "../../i18n/strings";
import { LocationMap } from "./LocationMap";
import "./location.css";

type At = [number, number];
const HAT_YAI = { lat: 7.0086, lng: 100.4747 };

/**
 * Pick your spot on a Google Map: pan and zoom to your street, tap to drop the pin, drag it to adjust.
 * No zones to choose; the server snaps the pin to segment and landmark. Without a Maps key, or if the map can't
 * load, the drawn map is shown instead.
 */
export function GoogleLocationPicker({ start, onConfirm }: { start?: At | null; onConfirm: (at: At) => void }) {
  const { t, lang } = useLang();
  const box = useRef<HTMLDivElement>(null);
  const [state, setState] = useState<"loading" | "ready" | "fallback">("loading");
  const [pin, setPin] = useState<At | null>(start ?? null);
  useEffect(() => {
    let alive = true;
    let marker: Maps;
    Promise.all([loadGoogleMaps(lang), demoBounds()])
      .then(([maps, [west, south, east, north]]) => {
        if (!alive || !box.current) return;
        const centre = start ? { lat: start[1], lng: start[0] } : HAT_YAI;
        const map = new maps.Map(box.current, {
          center: centre, zoom: start ? 17 : 14, clickableIcons: false, gestureHandling: "greedy",
          streetViewControl: false, mapTypeControl: false, fullscreenControl: false,
          restriction: { latLngBounds: { west, south, east, north }, strictBounds: false },
        });
        const place = (lat: number, lng: number) => {
          if (!marker) {
            marker = new maps.Marker({ map, position: { lat, lng }, draggable: true, title: t(S.location.pin) });
            marker.addListener("dragend", () => {
              const p = marker.getPosition();
              setPin([p.lng(), p.lat()]);
            });
          } else marker.setPosition({ lat, lng });
          setPin([lng, lat]);
        };
        if (start) place(start[1], start[0]);
        map.addListener("click", (e: Maps) => place(e.latLng.lat(), e.latLng.lng()));
        setState("ready");
      })
      .catch(() => alive && setState("fallback"));
    return () => {
      alive = false;
      marker?.setMap(null);
    };
    // The map is built once per open; language changes reopen the picker.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  if (state === "fallback") return <LocationMap at={start ?? null} onConfirm={onConfirm} />;
  return (
    <div className="location-map is-picker is-google">
      <p className="fine-print" id="gmap-help">{t(S.location.googleHelp)}</p>
      <div className="location-gmap-frame">
        {/* Google Maps owns this div's children; React must never render inside it. */}
        <div ref={box} className="location-gmap" role="application" aria-label={t(S.location.mapLabel)} aria-describedby="gmap-help" />
        {state === "loading" && <p role="status" className="location-gmap-loading">{t(S.briefing.mapLoading)}</p>}
      </div>
      <button type="button" className="btn btn-primary" disabled={!pin} onClick={() => pin && onConfirm(pin)}>
        {t(S.location.useSpot)}
      </button>
    </div>
  );
}
