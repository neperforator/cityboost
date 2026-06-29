import { ref } from 'vue'
import { userAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'
import type { User } from '@/types'

const users = ref<User[]>([])
const loaded = ref(false)
const loading = ref(false)

export function useUsers() {
  async function fetchUsers(): Promise<void> {
    const auth = useAuthStore()
    if (!auth.isAdmin) return
    if (loaded.value) return
    loading.value = true
    try {
      // Load first 1000 users (covers 401) for the name cache
      const data = await userAPI.list(1, 1000)
      users.value = data.items
      loaded.value = true
    } catch {
      // fallback: keep empty
    } finally {
      loading.value = false
    }
  }

  function getUserName(id: string): string {
    const u = users.value.find(user => user.id === id)
    return u ? u.name : 'Неизвестно'
  }

  function getUserDisplay(id: string): string {
    const u = users.value.find(user => user.id === id)
    if (!u) return 'Неизвестно'
    return `${u.name} (${u.email})`
  }

  function getUser(id: string): User | null {
    return users.value.find(user => user.id === id) || null
  }

  return {
    users,
    loaded,
    loading,
    fetchUsers,
    getUserName,
    getUserDisplay,
    getUser,
  }
}
