/* ================================================================
   CityBoost — TypeScript types and interfaces
   ================================================================ */

// ---- User ----

export interface User {
  id: string
  name: string
  email: string
  role: 'user' | 'admin'
  is_banned: boolean
  is_verified?: boolean
  created_at?: string
  updated_at?: string
}

// ---- Auth ----

export interface LoginResponse {
  access_token?: string
  token_type: string
  requires_2fa?: boolean
  challenge_token?: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface Admin2FAResendResponse {
  message: string
}

export interface VerifyCodePayload {
  email: string
  code: string
}

export interface VerifyCodeResponse {
  access_token?: string
  token_type: string
  user: User
  requires_2fa?: boolean
  challenge_token?: string
}

export interface UserUpdatePayload {
  name?: string
  current_password?: string
  new_password?: string
}

// ---- Tickets ----

export type TicketStatus = 'NEW' | 'IN_WORK' | 'DONE' | 'CLOSED'

export interface Ticket {
  id: string
  title: string
  description?: string
  address: string
  category: string
  status: TicketStatus
  latitude?: number | null
  longitude?: number | null
  close_reason?: string | null
  notify_author?: boolean
  user_id: string
  user_name?: string
  assigned_to?: string | null
  assigned_to_name?: string | null
  created_at: string
  updated_at?: string
  files?: TicketFile[]
  comments?: TicketComment[]
}

export interface BulkTicketSkip {
  ticket_id: string
  title?: string | null
  reason: string
}

export interface BulkTicketResult {
  updated: number
  skipped: number
  failed: number
  errors: Array<{ ticket_id: string; detail: string }>
  skipped_items: BulkTicketSkip[]
}

export interface TicketFile {
  id: string
  ticket_id: string
  file_path: string
  file_name: string
  file_size: number
  mime_type: string
  created_at: string
}

export interface TicketComment {
  id: string
  ticket_id: string
  author_id: string
  author_name: string
  author_role?: string
  comment_text: string
  created_at: string
}

export interface TicketCreatePayload {
  title: string
  description: string
  address: string
  category: string
  latitude?: number | null
  longitude?: number | null
  notify_author?: boolean
}

export interface TicketFilters {
  status?: TicketStatus
  page?: number
  page_size?: number
  q?: string
  assignee?: 'me' | 'unassigned' | 'all'
  overdue?: boolean
}

export interface TicketStatusChangePayload {
  new_status: TicketStatus
  close_reason?: string
}

// ---- Admin ----

export interface AdminActionLog {
  id: string
  admin_id: string
  admin_name?: string
  action: string
  target_type: string
  target_id: string
  target_name?: string | null
  details?: string
  created_at: string
}

export interface AdminDashboardStats {
  assigned: {
    total: number
    new: number
    in_work: number
    done: number
    closed: number
  }
  queue: number
  overdue: number
  recent_assigned: Ticket[]
  queue_tickets: Ticket[]
  recent_activity: AdminActionLog[]
}

export interface TicketHistoryEntry {
  id: string
  ticket_id: string
  changed_by: string
  changed_by_name?: string
  action?: string
  old_status?: string | null
  new_status?: string | null
  details?: string | null
  created_at: string
}

export interface AuditLogFilters {
  action?: string
  page?: number
  page_size?: number
  mine?: boolean
}

// ---- Analytics ----

export interface AnalyticsSummary {
  created_in_period: number
  resolved_in_period: number
  resolved_from_period: number
  open_now: number
  overdue_now: number
  backlog_start: number
  backlog_end: number
  resolution_rate: number
  avg_resolution_hours: number | null
  median_resolution_hours: number | null
  created_prev_period: number
  resolved_prev_period: number
  avg_resolution_prev_hours: number | null
  created_delta_pct: number | null
  resolved_delta_pct: number | null
  avg_resolution_delta_pct: number | null
}

export interface AnalyticsDayPoint {
  date: string
  created: number
  resolved: number
  backlog: number
}

export interface AnalyticsStatusPoint {
  status: TicketStatus
  label: string
  count: number
  percent: number
}

export interface AnalyticsAssigneePoint {
  admin_id: string
  name: string
  created_in_period: number
  resolved_in_period: number
  open_now: number
  overdue: number
  avg_resolution_hours: number | null
}

export interface AdminAnalytics {
  period_days: number
  generated_at: string
  summary: AnalyticsSummary
  by_day: AnalyticsDayPoint[]
  by_status: AnalyticsStatusPoint[]
  by_assignee: AnalyticsAssigneePoint[]
  assignees_total: number
}

export interface TicketMapPoint {
  id: string
  title: string
  status: TicketStatus
  latitude: number
  longitude: number
  address: string | null
  assigned_to_name: string | null
  created_at: string
}

export interface TicketMapResponse {
  items: TicketMapPoint[]
  total: number
  limit: number
}

export interface TicketMapFilters {
  status?: TicketStatus
  days?: number
  limit?: number
  q?: string
  assignee?: 'all' | 'me' | 'unassigned'
  overdue?: boolean
}

// ---- Common ----

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages?: number
  status_counts?: {
    NEW: number
    IN_WORK: number
    DONE: number
    CLOSED: number
    total: number
  }
}

// ---- Toast ----

export interface Toast {
  id: number
  message: string
  type: 'success' | 'error' | 'info' | 'warning'
  duration: number
}
