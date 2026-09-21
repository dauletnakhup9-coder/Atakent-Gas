export type Status = "NEW" | "IN_PROGRESS" | "COMPLETED" | "REJECTED";
export type Priority = "NORMAL" | "HIGH" | "CRITICAL";
export type ApplicationType = "METER_NOT_WORKING" | "MPI_REMOVAL" | "GAS_LEAK";
export type Role = "SUPER_ADMIN" | "DISPATCHER" | "OPERATOR";
export type Admin = {
  id: number;
  name: string;
  email: string;
  role: Role;
  active: boolean;
};
export type Application = {
  id: number;
  application_number: string;
  personal_account: string;
  application_type: ApplicationType;
  status: Status;
  priority: Priority;
  created_at: string;
  updated_at: string;
  assigned_to: number | null;
  assignee_name: string | null;
  requested_date: string | null;
  latitude: number | null;
  longitude: number | null;
  version: number;
  admin_comment: string | null;
  subscriber_verified?: boolean;
  user: {
    telegram_user_id: number;
    telegram_username: string | null;
    first_name: string;
    last_name: string | null;
  };
  files?: { id: string; file_type: string; url: string }[];
};
export type ApplicationList = {
  items: Application[];
  total: number;
  page: number;
  page_size: number;
};
export type Stats = {
  total: number;
  NEW: number;
  IN_PROGRESS: number;
  COMPLETED: number;
  REJECTED: number;
  critical: number;
  average_processing_hours: number | null;
  by_type: { type: ApplicationType; count: number }[];
  daily: { date: string; count: number }[];
};
export type History = {
  id: number;
  admin_name: string | null;
  old_status: Status | null;
  new_status: Status;
  comment: string | null;
  public_comment: boolean;
  created_at: string;
};
export type Settings = {
  organization_name: string;
  contact_phone: string;
  emergency_phone: string;
  max_photo_mb: number;
  notification_texts: Record<string, string>;
};
export const STATUS_LABELS: Record<Status, string> = {
  NEW: "Жаңа",
  IN_PROGRESS: "Өңделуде",
  COMPLETED: "Аяқталды",
  REJECTED: "Қабылданбады",
};
export const TYPE_LABELS: Record<ApplicationType, string> = {
  METER_NOT_WORKING: "Счетчик жұмыс жасамайды",
  MPI_REMOVAL: "МПИ-ге шешу",
  GAS_LEAK: "Есептеу құралынан газ шығуы",
};
export const PRIORITY_LABELS: Record<Priority, string> = {
  NORMAL: "Қалыпты",
  HIGH: "Жоғары",
  CRITICAL: "Авариялық",
};
export const ROLE_LABELS: Record<Role, string> = {
  SUPER_ADMIN: "Бас әкімші",
  DISPATCHER: "Диспетчер",
  OPERATOR: "Оператор",
};
