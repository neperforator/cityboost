import { defineStore } from 'pinia'
import { authAPI, getAccessToken, setAccessToken } from '@/api'
import router from '@/router'
import type { User, VerifyCodeResponse } from '@/types'

interface AuthState {
  user: User | null
  token: string | null
  loading: boolean
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: JSON.parse(localStorage.getItem('cityboost_user') || 'null'),
    token: getAccessToken(),
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
    async login(
      email: string,
      password: string,
    ): Promise<{ requires2FA: boolean; challengeToken?: string }> {
      this.loading = true
      try {
        const data = await authAPI.login(email, password)

        // Администратору токены ещё не выданы — сначала код из письма.
        if (data.requires_2fa) {
          return {
            requires2FA: true,
            challengeToken: data.challenge_token,
          }
        }

        if (!data.access_token) {
          throw new Error('Сервер не вернул access-токен')
        }
        this.token = data.access_token
        setAccessToken(data.access_token)
        // Refresh token в httpOnly cookie — JS его не видит
        await this.fetchMe()
        return { requires2FA: false }
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
      try {
        // Refresh token отправляется через httpOnly cookie автоматически
        const data = await authAPI.refresh()
        this.token = data.access_token
        setAccessToken(data.access_token)
        return true
      } catch {
        this.clearAuth()
        return false
      }
    },
    async bootstrap(): Promise<void> {
      // На старте access-токена в памяти нет: восстанавливаем сессию по refresh-cookie.
      if (this.token) {
        await this.fetchMe()
        return
      }
      const refreshed = await this.refreshTokens()
      if (refreshed) await this.fetchMe()
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
    async verifyEmail(email: string, code: string): Promise<VerifyCodeResponse> {
      this.loading = true
      try {
        const data = await authAPI.verifyEmail(email, code)

        // Администратору после подтверждения email всё равно нужен вход с 2FA.
        if (data.requires_2fa) {
          return data
        }

        if (!data.access_token) {
          throw new Error('Сервер не вернул access-токен')
        }
        this.token = data.access_token
        this.user = data.user
        setAccessToken(data.access_token)
        localStorage.setItem('cityboost_user', JSON.stringify(data.user))
        // Refresh token в httpOnly cookie — JS его не видит
        return data
      } catch (err) {
        throw err
      } finally {
        this.loading = false
      }
    },

    async resendCode(email: string): Promise<void> {
      await authAPI.resendCode(email)
    },

    async verifyAdmin2FA(challengeToken: string, code: string): Promise<void> {
      this.loading = true
      try {
        const data = await authAPI.verifyAdmin2FA(challengeToken, code)
        if (!data.access_token) {
          throw new Error('Сервер не вернул access-токен')
        }
        this.token = data.access_token
        setAccessToken(data.access_token)
        await this.fetchMe()
      } finally {
        this.loading = false
      }
    },

    async resendAdmin2FA(challengeToken: string): Promise<void> {
      await authAPI.resendAdmin2FA(challengeToken)
    },

    async logout(): Promise<void> {
      // Вызываем API чтобы очистить refresh cookie на сервере
      try { await authAPI.logout() } catch { /* неважно */ }
      this.clearAuth()
      router.push('/login')
    },
    clearAuth(): void {
      this.user = null
      this.token = null
      setAccessToken(null)
      localStorage.removeItem('cityboost_user')
    },
  },
})
