import { Badge } from "@/components/ui/badge";
import { STATUS_LABELS, type ApplicationStatus } from "@/lib/types";

const VARIANT_BY_STATUS: Record<ApplicationStatus, "default" | "warning" | "success" | "destructive"> = {
  NEW: "default",
  IN_PROGRESS: "warning",
  COMPLETED: "success",
  REJECTED: "destructive",
};

export function StatusBadge({ status }: { status: ApplicationStatus }) {
  return <Badge variant={VARIANT_BY_STATUS[status]}>{STATUS_LABELS[status]}</Badge>;
}
