"use client";
import { useEffect, useRef } from "react";

export interface Pick {
  lat: number;
  lon: number;
}

export default function CheckoutMap({ onPick }: { onPick: (p: Pick) => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const box = useRef<{ locate: () => void } | null>(null);
  const cb = useRef(onPick);
  cb.current = onPick;

  useEffect(() => {
    let alive = true;
    (async () => {
      const L = (await import("leaflet")).default;
      if (!alive || !ref.current || box.current) return;
      const map = L.map(ref.current).setView([41.3111, 69.2797], 12);
      L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
      }).addTo(map);
      const icon = L.divIcon({
        html: "<div style='font-size:28px;line-height:1'>📍</div>",
        className: "",
        iconSize: [28, 28],
        iconAnchor: [14, 26],
      });
      let marker: ReturnType<typeof L.marker> | null = null;
      const place = (lat: number, lon: number) => {
        const ll = { lat, lng: lon } as never;
        if (marker) marker.setLatLng(ll);
        else marker = L.marker(ll, { icon }).addTo(map);
        cb.current({ lat: +lat.toFixed(6), lon: +lon.toFixed(6) });
      };
      map.on("click", (e: { latlng: { lat: number; lng: number } }) => place(e.latlng.lat, e.latlng.lng));
      box.current = {
        locate() {
          if (!navigator.geolocation) return;
          navigator.geolocation.getCurrentPosition(
            (p) => {
              map.setView([p.coords.latitude, p.coords.longitude], 15);
              place(p.coords.latitude, p.coords.longitude);
            },
            () => {},
            { timeout: 10000 }
          );
        },
      };
      setTimeout(() => map.invalidateSize(), 300);
    })();
    return () => {
      alive = false;
    };
  }, []);

  return (
    <div>
      <div ref={ref} className="h-[230px] rounded-xl border border-beige relative z-0 bg-ivory" />
      <div className="flex gap-2 items-center mt-2 flex-wrap">
        <button type="button" onClick={() => box.current?.locate()} className="btn btn-outline !py-2 text-xs">
          📍 Meni topish
        </button>
      </div>
    </div>
  );
}
