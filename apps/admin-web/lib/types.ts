export type ApplicationType = "METER_NOT_WORKING" | "MPI_REMOVAL" | "GAS_LEAK";
export type ApplicationStatus = "NEW" | "IN_PROGRESS" | "COMPLETED" | "REJECTED";
export type Priority = "NORMAL" | "HIGH" | "CRITICAL";
export type AdminRole = "SUPER_ADMIN" | "DISPATCHER" | "OPERATOR";
export type FileType = "METER_PHOTO" | "GAS_LEAK_PHOTO" | "OTHER";

export const APPLICATION_TYPE_LABELS: Record<ApplicationType, string> = {
  METER_NOT_WORKING: "Счетчик жұмыс жасамайды",
  MPI_REMOVAL: "МПИ-ге шешу",
  GAS_LEAK: "Есептеу құралынан газ шығуы",
};

export const STATUS_LABELS: Record<ApplicationStatus, string> = {
  NEW: "🆕 Жаңа",
  IN_PROGRESS: "🟡 Өңделуде",
  COMPLETED: "🟢 Аяқталды",
  REJECTED: "🔴 Қабылданбады",
};

export const PRIORITY_LABELS: Record<Priority, string> = {
  NORMAL: "Қалыпты",
  HIGH: "Жоғары",
  CRITICAL: "🚨 АВАРИЯ",
};

export const ROLE_LABELS: Record<AdminRole, string> = {
  SUPER_ADMIN: "Супер-администратор",
  DISPATCHER: "Диспетчер",
  OPERATOR: "Оператор",
};

export interface AdminOut {
  id: number;
  name: string;
  email: string;
  role: AdminRole;
  active: boolean;
}

export interface UserOut {
  id: number;
  telegram_user_id: number;
  telegram_username: string | null;
  first_name: string | null;
  last_name: string | null;
}

export interface ApplicationFileOut {
  id: number;
  file_type: FileType;
  storage_url: string;
  created_at: string;
}

export interface ApplicationHistoryOut {
  id: number;
  old_status: ApplicationStatus | null;
  new_status: ApplicationStatus;
  comment: string | null;
  admin_name: string | null;
  created_at: string;
}

export interface ApplicationOut {
  id: number;
  application_number: string;
  personal_account: string;
  application_type: ApplicationType;
  status: ApplicationStatus;
  priority: Priority;
  requested_date: string | null;
  latitude: number | null;
  longitude: number | null;
  admin_comment: string | null;
  created_at: string;
  updated_at: string;
  user: UserOut;
  assigned_admin: { id: number; name: string } | null;
}

export interface ApplicationDetailOut extends ApplicationOut {
  files: ApplicationFileOut[];
  history: ApplicationHistoryOut[];
}

export interface ApplicationListOut {
  items: ApplicationOut[];
  total: number;
  page: number;
  page_size: number;
}

export interface DashboardStats {
  total: number;
  new: number;
  in_progress: number;
  completed: number;
  rejected: number;
  critical: number;
  type_distribution: Record<string, number>;
  daily_counts: { date: string; count: number }[];
}
