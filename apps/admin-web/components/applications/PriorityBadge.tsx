import { Badge } from "@/components/ui/badge";
import { PRIORITY_LABELS, type Priority } from "@/lib/types";

export function PriorityBadge({ priority }: { priority: Priority }) {
  if (priority === "CRITICAL") return <Badge variant="critical">{PRIORITY_LABELS.CRITICAL}</Badge>;
  if (priority === "HIGH") return <Badge variant="warning">{PRIORITY_LABELS.HIGH}</Badge>;
  return <Badge variant="secondary">{PRIORITY_LABELS.NORMAL}</Badge>;
}
