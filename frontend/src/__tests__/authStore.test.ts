import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

describe('AuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('starts unauthenticated', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
  })

  it('loads token from localStorage', () => {
    localStorage.setItem('cityboost_token', 'test-token')
    localStorage.setItem('cityboost_user', JSON.stringify({
      id: '1', name: 'Test', email: 'test@test.com', role: 'user',
    }))
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(true)
    expect(store.token).toBe('test-token')
    expect(store.userName).toBe('Test')
  })

  it('detects admin role', () => {
    localStorage.setItem('cityboost_user', JSON.stringify({
      id: '1', name: 'Admin', email: 'admin@test.com', role: 'admin',
    }))
    const store = useAuthStore()
    expect(store.isAdmin).toBe(true)
  })

  it('clearAuth clears everything', () => {
    localStorage.setItem('cityboost_token', 'test')
    localStorage.setItem('cityboost_user', JSON.stringify({ id: '1' }))
    const store = useAuthStore()
    store.clearAuth()
    expect(store.token).toBeNull()
    expect(store.user).toBeNull()
    expect(localStorage.getItem('cityboost_token')).toBeNull()
    expect(localStorage.getItem('cityboost_user')).toBeNull()
  })
})
