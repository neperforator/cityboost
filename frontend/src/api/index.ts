import axios, { type AxiosError } from 'axios'
import type { PaginatedResponse, Ticket, TicketFilters, LoginResponse, User, AdminActionLog, AuditLogFilters, TicketComment } from '@/types'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cityboost_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err: AxiosError<{ detail?: string; error?: string }>) => {
    const status = err.response?.status
    const detail = err.response?.data?.detail || ''
    const errorText = err.response?.data?.error || detail || err.message || 'Ошибка запроса'

    if (status === 403 && detail.includes('заблокирован')) {
      localStorage.removeItem('cityboost_token')
      localStorage.removeItem('cityboost_user')
      window.location.hash = '#/login'
      return Promise.reject(new Error('Ваш аккаунт заблокирован администратором'))
    }

    if (status === 401 && !window.location.hash.startsWith('#/login')) {
      localStorage.removeItem('cityboost_token')
      localStorage.removeItem('cityboost_user')
      window.location.hash = '#/login'
    }

    return Promise.reject(new Error(errorText))
  }
)

export default api

// ---- Auth ----

export interface AuthAPI {
  register(name: string, email: string, password: string): Promise<unknown>
  login(email: string, password: string): Promise<LoginResponse>
  me(): Promise<User>
  updateProfile(data: Partial<{ name: string; current_password: string; new_password: string }>): Promise<User>
  forgotPassword(email: string): Promise<{ message: string }>
  resetPassword(token: string, password: string): Promise<{ message: string }>
}

export const authAPI: AuthAPI = {
  register(name, email, password) {
    return api.post('/auth/register', { name, email, password }).then(r => r.data)
  },
  login(email, password) {
    return api.post('/auth/login', { email, password }).then(r => r.data)
  },
  me() {
    return api.get('/auth/me').then(r => r.data)
  },
  updateProfile(data) {
    return api.patch('/auth/me', data).then(r => r.data)
  },
  forgotPassword(email) {
    return api.post('/auth/forgot-password', { email }).then(r => r.data)
  },
  resetPassword(token, password) {
    return api.post('/auth/reset-password', { token, password }).then(r => r.data)
  },
}

// ---- Tickets ----

export interface TicketAPI {
  list(page?: number, pageSize?: number, status?: string): Promise<PaginatedResponse<Ticket>>
  get(id: string): Promise<Ticket>
  create(formData: FormData): Promise<Ticket>
  uploadFile(ticketId: string, file: File): Promise<unknown>
  addComment(ticketId: string, text: string): Promise<TicketComment>
  getStats(): Promise<{ total: number; new: number; in_work: number; done: number; closed: number }>
}

export const ticketAPI: TicketAPI = {
  list(page = 1, pageSize = 20, status?: string) {
    let url = `/tickets?page=${page}&page_size=${pageSize}`
    if (status) url += `&status=${status}`
    return api.get(url).then(r => r.data)
  },
  get(id) {
    return api.get(`/tickets/${id}`).then(r => r.data)
  },
  create(formData) {
    return api.post('/tickets', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },
  uploadFile(ticketId, file) {
    const fd = new FormData()
    fd.append('file', file)
    return api.post(`/tickets/${ticketId}/files`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },
  addComment(ticketId, text) {
    return api.post(`/tickets/${ticketId}/comments`, { comment_text: text }).then(r => r.data)
  },
  getStats() {
    return api.get('/tickets/stats').then(r => r.data)
  },
}

// ---- Users ----

export interface UserAPI {
  list(page?: number, pageSize?: number, search?: string): Promise<PaginatedResponse<User>>
  changeRole(userId: string, role: string): Promise<User>
  ban(userId: string): Promise<User>
  unban(userId: string): Promise<User>
}

export const userAPI: UserAPI = {
  list(page = 1, pageSize = 20, search?: string) {
    let url = `/admin/users?page=${page}&page_size=${pageSize}`
    if (search) url += `&search=${encodeURIComponent(search)}`
    return api.get(url).then(r => r.data)
  },
  changeRole(userId, role) {
    return api.patch(`/admin/users/${userId}/role?new_role=${role}`).then(r => r.data)
  },
  ban(userId) {
    return api.patch(`/admin/users/${userId}/ban`).then(r => r.data)
  },
  unban(userId) {
    return api.patch(`/admin/users/${userId}/unban`).then(r => r.data)
  },
}

// ---- Admin ----

export interface AdminAPI {
  listTickets(params?: TicketFilters): Promise<PaginatedResponse<Ticket>>
  getTicket(id: string): Promise<Ticket>
  changeStatus(id: string, status: string): Promise<Ticket>
  assign(id: string): Promise<Ticket>
  addComment(id: string, text: string): Promise<TicketComment>
  getHistory(id: string): Promise<unknown[]>
  getAuditLogs(params?: AuditLogFilters): Promise<PaginatedResponse<AdminActionLog>>
  getStats(): Promise<{ total: number; new: number; in_work: number; done: number; closed: number }>
}

export const adminAPI: AdminAPI = {
  listTickets(params = {}) {
    const q = new URLSearchParams()
    if (params.status) q.set('status', params.status)
    if (params.page) q.set('page', String(params.page))
    if (params.page_size) q.set('page_size', String(params.page_size))
    return api.get(`/admin/tickets?${q}`).then(r => r.data)
  },
  getTicket(id) {
    return api.get(`/admin/tickets/${id}`).then(r => r.data)
  },
  changeStatus(id, status) {
    return api.patch(`/admin/tickets/${id}/status?new_status=${status}`).then(r => r.data)
  },
  assign(id) {
    return api.patch(`/admin/tickets/${id}/assign`).then(r => r.data)
  },
  addComment(id, text) {
    return api.post(`/admin/tickets/${id}/comments`, { comment_text: text }).then(r => r.data)
  },
  getHistory(id) {
    return api.get(`/admin/tickets/${id}/history`).then(r => r.data)
  },
  getAuditLogs(params = {}) {
    const q = new URLSearchParams()
    if (params.page) q.set('page', String(params.page))
    if (params.page_size) q.set('page_size', String(params.page_size))
    if (params.action) q.set('action', params.action)
    return api.get(`/admin/audit-logs?${q}`).then(r => r.data)
  },
  getStats() {
    return api.get('/admin/tickets/stats').then(r => r.data)
  },
}
