import { defineStore } from 'pinia'
import { authAPI } from '@/api'
import router from '@/router'
import type { User } from '@/types'

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  loading: boolean
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: JSON.parse(localStorage.getItem('cityboost_user') || 'null'),
    token: localStorage.getItem('cityboost_token') || null,
    refreshToken: localStorage.getItem('cityboost_refresh') || null,
    loading: false,
  }),
  getters: {
    isAuthenticated: (state): boolean => !!state.token,
    isAdmin: (state): boolean => state.user?.role === 'admin',
    userName: (state): string => state.user?.name || '',
    userEmail: (state): string => state.user?.email || '',
    userRole: (state): string => state.user?.role || '',
  },
  actions: {
    async login(email: string, password: string): Promise<boolean> {
      this.loading = true
      try {
        const data = await authAPI.login(email, password)
        this.token = data.access_token
        this.refreshToken = data.refresh_token
        localStorage.setItem('cityboost_token', data.access_token)
        localStorage.setItem('cityboost_refresh', data.refresh_token)
        await this.fetchMe()
        return true
      } catch (err) {
        throw err
      } finally {
        this.loading = false
      }
    },
    async register(name: string, email: string, password: string): Promise<boolean> {
      this.loading = true
      try {
        await authAPI.register(name, email, password)
        return true
      } catch (err) {
        throw err
      } finally {
        this.loading = false
      }
    },
    async refreshTokens(): Promise<boolean> {
      const currentRefreshToken = this.refreshToken || localStorage.getItem('cityboost_refresh')
      if (!currentRefreshToken) return false
      try {
        const data = await authAPI.refresh(currentRefreshToken)
        this.token = data.access_token
        this.refreshToken = data.refresh_token
        localStorage.setItem('cityboost_token', data.access_token)
        localStorage.setItem('cityboost_refresh', data.refresh_token)
        return true
      } catch {
        this.clearAuth()
        return false
      }
    },
    async fetchMe(): Promise<User | null> {
      try {
        const user = await authAPI.me()
        this.user = user
        localStorage.setItem('cityboost_user', JSON.stringify(user))
        return user
      } catch {
        this.clearAuth()
        return null
      }
    },
    async verifyEmail(email: string, code: string): Promise<User | null> {
      this.loading = true
      try {
        const data = await authAPI.verifyEmail(email, code)
        this.token = data.access_token
        this.refreshToken = data.refresh_token
        this.user = data.user
        localStorage.setItem('cityboost_token', data.access_token)
        localStorage.setItem('cityboost_refresh', data.refresh_token)
        localStorage.setItem('cityboost_user', JSON.stringify(data.user))
        return data.user
      } catch (err) {
        throw err
      } finally {
        this.loading = false
      }
    },

    async resendCode(email: string): Promise<void> {
      await authAPI.resendCode(email)
    },

    logout(): void {
      this.clearAuth()
      router.push('/login')
    },
    clearAuth(): void {
      this.user = null
      this.token = null
      this.refreshToken = null
      localStorage.removeItem('cityboost_token')
      localStorage.removeItem('cityboost_refresh')
      localStorage.removeItem('cityboost_user')
    },
  },
})
