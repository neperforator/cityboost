import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { getAccessToken, setAccessToken } from '@/api'
import { useAuthStore } from '@/stores/auth'

describe('AuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    setAccessToken(null)
  })

  it('starts unauthenticated', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
  })

  it('uses in-memory access token and restores user from localStorage', () => {
    setAccessToken('test-token')
    localStorage.setItem('cityboost_user', JSON.stringify({
      id: '1', name: 'Test', email: 'test@test.com', role: 'user',
    }))
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(true)
    expect(store.token).toBe('test-token')
    expect(store.userName).toBe('Test')
    // Access-токен не должен попадать в localStorage.
    expect(localStorage.getItem('cityboost_token')).toBeNull()
  })

  it('detects admin role', () => {
    localStorage.setItem('cityboost_user', JSON.stringify({
      id: '1', name: 'Admin', email: 'admin@test.com', role: 'admin',
    }))
    const store = useAuthStore()
    expect(store.isAdmin).toBe(true)
  })

  it('clearAuth clears token, user and memory', () => {
    setAccessToken('test')
    localStorage.setItem('cityboost_user', JSON.stringify({ id: '1' }))
    const store = useAuthStore()
    store.clearAuth()
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(getAccessToken()).toBeNull()
    expect(localStorage.getItem('cityboost_user')).toBeNull()
  })
})
