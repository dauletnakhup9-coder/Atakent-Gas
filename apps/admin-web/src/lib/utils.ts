import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
export function dateTime(value: string) {
  return new Intl.DateTimeFormat("kk-KZ", {
    timeZone: "Asia/Qyzylorda",
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
export function dateOnly(value: string) {
  return new Intl.DateTimeFormat("kk-KZ", {
    dateStyle: "medium",
    timeZone: "UTC",
  }).format(new Date(value + "T00:00:00Z"));
}
