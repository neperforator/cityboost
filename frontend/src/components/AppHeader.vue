<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

defineProps({ dark: Boolean })
defineEmits(['toggleDark'])

const auth = useAuthStore()
const router = useRouter()
const mobileOpen = ref(false)
const adminDropdownOpen = ref(false)

const initials = computed(() => {
  if (!auth.userName) return '?'
  return auth.userName.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
})

const navLinks = computed(() => {
  const links = [
    { to: '/dashboard', label: 'Мои заявки', icon: '📋' },
  ]
  links.push({ to: '/about', label: 'О проекте', icon: 'ℹ️' })
  return links
})

const adminLinks = [
  { to: '/admin', label: 'Все заявки', icon: '📋', desc: 'Управление всеми заявками' },
  { to: '/admin/users', label: 'Пользователи', icon: '👥', desc: 'Управление пользователями' },
  { to: '/admin/audit', label: 'Аудит-лог', icon: '📋', desc: 'История действий админов' },
]

const activeRoute = computed(() => router.currentRoute.value.path)

function go(to) {
  router.push(to)
  mobileOpen.value = false
  adminDropdownOpen.value = false
}

function isAdminActive() {
  return activeRoute.value.startsWith('/admin')
}

// Close dropdown on click outside
function onClickOutside(e) {
  const el = document.getElementById('admin-dropdown')
  if (el && !el.contains(e.target)) {
    adminDropdownOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>

<template>
  <header class="sticky top-0 z-50 bg-gradient-to-r from-indigo-900 via-indigo-800 to-blue-900 shadow-lg">
    <div class="max-w-7xl mx-auto px-4 sm:px-6">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <router-link to="/dashboard" class="flex items-center gap-2 text-white font-extrabold text-xl tracking-tight hover:opacity-90 transition-opacity">
          <span class="text-2xl">🏙️</span>
          <span>CityBoost</span>
        </router-link>

        <!-- Desktop nav -->
        <nav class="hidden md:flex items-center gap-1">
          <router-link
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            class="px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="activeRoute === link.to
              ? 'text-white bg-white/15'
              : 'text-indigo-200 hover:text-white hover:bg-white/10'"
          >
            {{ link.icon }} {{ link.label }}
          </router-link>

          <!-- Admin dropdown -->
          <div v-if="auth.isAdmin" id="admin-dropdown" class="relative">
            <button
              @click.stop="adminDropdownOpen = !adminDropdownOpen"
              class="px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5"
              :class="isAdminActive()
                ? 'text-white bg-white/15'
                : 'text-indigo-200 hover:text-white hover:bg-white/10'"
            >
              ⚙️ Админка
              <svg class="w-3.5 h-3.5 transition-transform" :class="{ 'rotate-180': adminDropdownOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
            </button>

            <!-- Dropdown -->
            <Transition name="dropdown">
              <div v-if="adminDropdownOpen" class="absolute right-0 mt-2 w-72 bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 py-2 overflow-hidden">
                <div class="px-4 py-2 border-b border-gray-100 dark:border-gray-700">
                  <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Админ-панель</p>
                </div>
                <router-link
                  v-for="link in adminLinks"
                  :key="link.to"
                  :to="link.to"
                  @click="go(link.to)"
                  class="flex items-start gap-3 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                  :class="activeRoute === link.to ? 'bg-primary-50 dark:bg-primary-900/20' : ''"
                >
                  <span class="text-lg mt-0.5">{{ link.icon }}</span>
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">{{ link.label }}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">{{ link.desc }}</p>
                  </div>
                </router-link>
                <div class="border-t border-gray-100 dark:border-gray-700 mt-1 pt-1 px-2">
                  <router-link
                    to="/admin"
                    @click="adminDropdownOpen = false"
                    class="flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                  >
                    📊 Статистика: {{ auth.userName }}
                  </router-link>
                </div>
              </div>
            </Transition>
          </div>
        </nav>

        <!-- Right side: dark mode + user -->
        <div class="flex items-center gap-3">
          <button @click="$emit('toggleDark')" class="p-2 rounded-lg text-indigo-200 hover:text-white hover:bg-white/10 transition-colors" :title="dark ? 'Светлая тема' : 'Тёмная тема'">
            <svg v-if="dark" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
          </button>

          <div v-if="auth.isAuthenticated" class="flex items-center gap-3">
            <router-link to="/profile" class="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm text-indigo-200 hover:text-white hover:bg-white/10 transition-colors">
              <template v-if="auth.user?.avatar_path">
                <img :src="`/storage/${auth.user.avatar_path}`" class="w-7 h-7 rounded-full object-cover" :alt="auth.userName" />
              </template>
              <span v-else class="w-7 h-7 rounded-full bg-indigo-500 flex items-center justify-center text-xs font-bold text-white">{{ initials }}</span>
              <span class="hidden lg:inline">{{ auth.userName }}</span>
            </router-link>
            <button @click="auth.logout()" class="px-3 py-1.5 rounded-lg text-sm font-medium text-indigo-200 hover:text-white hover:bg-white/10 border border-white/20 transition-colors">Выйти</button>
          </div>

          <button @click="mobileOpen = !mobileOpen" class="md:hidden p-2 rounded-lg text-indigo-200 hover:text-white hover:bg-white/10">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path v-if="!mobileOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
              <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Mobile menu -->
      <div v-if="mobileOpen" class="md:hidden pb-4 border-t border-white/10 pt-3">
        <div class="flex flex-col gap-1">
          <router-link to="/dashboard" @click="mobileOpen = false" class="px-3 py-2.5 rounded-lg text-sm font-medium" :class="activeRoute === '/dashboard' ? 'text-white bg-white/15' : 'text-indigo-200 hover:text-white hover:bg-white/10'">📋 Мои заявки</router-link>
          <template v-if="auth.isAdmin">
            <p class="px-3 pt-2 pb-1 text-xs font-semibold text-indigo-300/60 uppercase tracking-wider">Админ-панель</p>
            <router-link to="/admin" @click="mobileOpen = false" class="px-3 py-2.5 rounded-lg text-sm font-medium text-indigo-200 hover:text-white hover:bg-white/10">📋 Все заявки</router-link>
            <router-link to="/admin/users" @click="mobileOpen = false" class="px-3 py-2.5 rounded-lg text-sm font-medium text-indigo-200 hover:text-white hover:bg-white/10">👥 Пользователи</router-link>
            <router-link to="/admin/audit" @click="mobileOpen = false" class="px-3 py-2.5 rounded-lg text-sm font-medium text-indigo-200 hover:text-white hover:bg-white/10">📋 Аудит-лог</router-link>
          </template>
          <router-link to="/profile" @click="mobileOpen = false" class="px-3 py-2.5 rounded-lg text-sm font-medium text-indigo-200 hover:text-white hover:bg-white/10">👤 Профиль</router-link>
          <router-link to="/about" @click="mobileOpen = false" class="px-3 py-2.5 rounded-lg text-sm font-medium text-indigo-200 hover:text-white hover:bg-white/10">ℹ️ О проекте</router-link>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.dropdown-enter-active, .dropdown-leave-active { transition: all 0.2s ease; }
.dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
