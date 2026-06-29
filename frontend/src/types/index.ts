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
  created_at?: string
  updated_at?: string
}

// ---- Auth ----

export interface LoginResponse {
  access_token: string
  token_type: string
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
  user_id: string
  user_name?: string
  assigned_to?: string | null
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
}

// ---- Admin ----

export interface AdminActionLog {
  id: string
  admin_id: string
  admin_name?: string
  action: string
  target_type: string
  target_id: string
  details?: string
  created_at: string
}

export interface AuditLogFilters {
  action?: string
  page?: number
  page_size?: number
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
