"use client";

import { useEffect, useRef } from "react";

import { getToken, wsUrl } from "@/lib/api";

export interface RealtimeEvent {
  type: "application_created" | "application_status_changed" | "application_assigned";
  data: Record<string, unknown>;
}

export function useRealtime(onEvent: (event: RealtimeEvent) => void) {
  const handlerRef = useRef(onEvent);
  handlerRef.current = onEvent;

  useEffect(() => {
    const token = getToken();
    if (!token) return;

    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let closedByClient = false;

    function connect() {
      socket = new WebSocket(`${wsUrl()}?token=${encodeURIComponent(token as string)}`);

      socket.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data) as RealtimeEvent;
          handlerRef.current(parsed);
        } catch {
          // ignore malformed payloads
        }
      };

      socket.onclose = () => {
        if (!closedByClient) {
          reconnectTimer = setTimeout(connect, 3000);
        }
      };

      socket.onerror = () => {
        socket?.close();
      };
    }

    connect();

    return () => {
      closedByClient = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, []);
}
