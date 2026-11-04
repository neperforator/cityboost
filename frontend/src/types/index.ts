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
  access_token: string
  token_type: string
}

export interface VerifyCodePayload {
  email: string
  code: string
}

export interface VerifyCodeResponse {
  access_token: string
  token_type: string
  user: User
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
  description: string
  address: string
  category: string
  status: TicketStatus
  latitude?: number | null
  longitude?: number | null
  close_reason?: string | null
  user_id: string
  user_name?: string
  assigned_to?: string | null
  assigned_to_name?: string | null
  created_at: string
  updated_at?: string
  files?: TicketFile[]
  comments?: TicketComment[]
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
