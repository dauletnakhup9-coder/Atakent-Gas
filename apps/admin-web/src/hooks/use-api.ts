"use client";
import { useEffect, useState } from "react";
import { api } from "@/services/api";
export function useApi<T>(path: string | null, revision = 0) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!path) {
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError("");
    api<T>(path, { signal: controller.signal })
      .then(setData)
      .catch((e) => {
        if (e.name !== "AbortError") {
          setError(e.message);
          setData(null);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [path, revision]);
  return { data, error, loading };
}
