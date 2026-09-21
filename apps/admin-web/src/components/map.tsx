"use client";
import { useEffect, useRef } from "react";
import "leaflet/dist/leaflet.css";
export default function Map({
  latitude,
  longitude,
}: {
  latitude: number;
  longitude: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let map: import("leaflet").Map | undefined,
      cancelled = false;
    import("leaflet").then((L) => {
      if (!ref.current || cancelled) return;
      map = L.map(ref.current).setView([latitude, longitude], 15);
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        referrerPolicy: "strict-origin-when-cross-origin",
        maxZoom: 19,
      }).addTo(map);
      L.circleMarker([latitude, longitude], {
        radius: 10,
        color: "#fff",
        fillColor: "#c54c40",
        fillOpacity: 1,
        weight: 3,
      }).addTo(map);
    });
    return () => {
      cancelled = true;
      map?.remove();
    };
  }, [latitude, longitude]);
  return (
    <div
      className="map"
      ref={ref}
      aria-label={`Өтінім орны: ${latitude}, ${longitude}`}
    />
  );
}
