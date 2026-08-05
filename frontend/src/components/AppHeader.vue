<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Bars3Icon, XMarkIcon, SunIcon, MoonIcon, ChevronDownIcon, ClipboardDocumentListIcon, UserCircleIcon, ArrowRightOnRectangleIcon, ShieldCheckIcon, UsersIcon, ClockIcon } from '@heroicons/vue/24/outline'
import { TicketIcon } from '@heroicons/vue/24/solid'

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
    { to: '/dashboard', label: 'Мои заявки', icon: ClipboardDocumentListIcon },
  ]
  links.push({ to: '/about', label: 'О проекте', icon: TicketIcon })
  return links
})

const adminLinks = [
  { to: '/admin', label: 'Все заявки', icon: ClipboardDocumentListIcon, desc: 'Управление всеми заявками' },
  { to: '/admin/users', label: 'Пользователи', icon: UsersIcon, desc: 'Управление пользователями' },
  { to: '/admin/audit', label: 'Аудит-лог', icon: ClockIcon, desc: 'История действий админов' },
]

const activeRoute = computed(() => router.currentRoute.value.path)

function go(to: string) {
  router.push(to)
  mobileOpen.value = false
  adminDropdownOpen.value = false
}

function isAdminActive() {
  return activeRoute.value.startsWith('/admin')
}

// Close dropdown on click outside
function onClickOutside(e: MouseEvent) {
  const el = document.getElementById('admin-dropdown')
  if (el && !el.contains(e.target as Node)) {
    adminDropdownOpen.value = false
  }
}

// Lock body scroll when mobile menu is open (only on mobile)
watch(mobileOpen, (val) => {
  if (window.innerWidth < 768) {
    document.documentElement.classList.toggle('overflow-hidden', val)
  }
})

onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>

<template>
  <header class="sticky top-0 z-50 bg-primary-700 dark:bg-primary-900 shadow-lg border-b border-primary-600/50 dark:border-primary-800/50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <router-link to="/dashboard" class="flex items-center gap-2.5 text-white font-bold text-lg tracking-tight hover:opacity-90 transition-opacity">
          <div class="w-8 h-8 rounded-lg bg-white/15 flex items-center justify-center">
            <TicketIcon class="w-5 h-5 text-white" />
          </div>
          <span class="font-extrabold text-xl">CityBoost</span>
        </router-link>

        <!-- Desktop nav -->
        <nav class="hidden md:flex items-center gap-1">
          <router-link
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
            :class="activeRoute === link.to
              ? 'text-white bg-white/15'
              : 'text-primary-200 hover:text-white hover:bg-white/10'"
          >
            <component :is="link.icon" class="w-4 h-4" />
            {{ link.label }}
          </router-link>

          <!-- Admin dropdown -->
          <div v-if="auth.isAdmin" id="admin-dropdown" class="relative">
            <button
              @click.stop="adminDropdownOpen = !adminDropdownOpen"
              class="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
              :class="isAdminActive()
                ? 'text-white bg-white/15'
                : 'text-primary-200 hover:text-white hover:bg-white/10'"
            >
              <ShieldCheckIcon class="w-4 h-4" />
              Админка
              <ChevronDownIcon class="w-3.5 h-3.5 transition-transform" :class="{ 'rotate-180': adminDropdownOpen }" />
            </button>

            <!-- Dropdown -->
            <Transition name="dropdown">
              <div v-if="adminDropdownOpen" class="absolute right-0 mt-2 w-72 bg-white dark:bg-gray-800 rounded-xl shadow-dropdown border border-gray-200 dark:border-gray-700 py-2 overflow-hidden">
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
                  <component :is="link.icon" class="w-5 h-5 text-gray-400 mt-0.5 shrink-0" />
                  <div>
                    <p class="text-sm font-medium text-gray-900 dark:text-white">{{ link.label }}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">{{ link.desc }}</p>
                  </div>
                </router-link>
              </div>
            </Transition>
          </div>
        </nav>

        <!-- Right side: dark mode + user -->
        <div class="flex items-center gap-2">
          <button @click="$emit('toggleDark')" class="p-2 rounded-lg text-primary-200 hover:text-white hover:bg-white/10 transition-colors" :title="dark ? 'Светлая тема' : 'Тёмная тема'">
            <SunIcon v-if="dark" class="w-5 h-5" />
            <MoonIcon v-else class="w-5 h-5" />
          </button>

          <div v-if="auth.isAuthenticated" class="flex items-center gap-2">
            <router-link to="/profile" class="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm text-primary-200 hover:text-white hover:bg-white/10 transition-colors">
              <span class="w-7 h-7 rounded-full bg-primary-500 flex items-center justify-center text-xs font-bold text-white">{{ initials }}</span>
              <span class="hidden lg:inline">{{ auth.userName }}</span>
            </router-link>
            <button @click="auth.logout()" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-primary-200 hover:text-white hover:bg-white/10 border border-primary-500/30 hover:border-primary-400/50 transition-colors">
              <ArrowRightOnRectangleIcon class="w-4 h-4" />
              <span class="hidden sm:inline">Выйти</span>
            </button>
          </div>

          <button @click="mobileOpen = !mobileOpen" class="md:hidden p-2 rounded-lg text-primary-200 hover:text-white hover:bg-white/10 active:scale-90 transition-all duration-200">
            <div class="relative w-6 h-6 flex items-center justify-center">
              <Transition name="burger-icon">
                <Bars3Icon v-if="!mobileOpen" key="bars" class="w-6 h-6 absolute" />
                <XMarkIcon v-else key="xmark" class="w-6 h-6 absolute" />
              </Transition>
            </div>
          </button>
        </div>
      </div>

      <!-- Mobile menu (smooth slide) -->
      <Transition name="mobile-menu">
        <div v-if="mobileOpen" class="md:hidden border-t border-primary-600/30 overflow-hidden">
          <div class="pb-4 pt-3 mobile-menu-content">
            <div class="flex flex-col gap-1">
              <router-link to="/dashboard" @click="mobileOpen = false" class="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium transition-all active:scale-[0.97]" :class="activeRoute === '/dashboard' ? 'text-white bg-white/15' : 'text-primary-200 hover:text-white hover:bg-white/10'">
                <ClipboardDocumentListIcon class="w-4 h-4" /> Мои заявки
              </router-link>
              <template v-if="auth.isAdmin">
                <p class="px-3 pt-2 pb-1 text-xs font-semibold text-primary-300/60 uppercase tracking-wider">Админ-панель</p>
                <router-link to="/admin" @click="mobileOpen = false" class="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-primary-200 hover:text-white hover:bg-white/10 transition-all active:scale-[0.97]">
                  <ClipboardDocumentListIcon class="w-4 h-4" /> Все заявки
                </router-link>
                <router-link to="/admin/users" @click="mobileOpen = false" class="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-primary-200 hover:text-white hover:bg-white/10 transition-all active:scale-[0.97]">
                  <UsersIcon class="w-4 h-4" /> Пользователи
                </router-link>
                <router-link to="/admin/audit" @click="mobileOpen = false" class="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-primary-200 hover:text-white hover:bg-white/10 transition-all active:scale-[0.97]">
                  <ClockIcon class="w-4 h-4" /> Аудит-лог
                </router-link>
              </template>
              <router-link to="/profile" @click="mobileOpen = false" class="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-primary-200 hover:text-white hover:bg-white/10 transition-all active:scale-[0.97]">
                <UserCircleIcon class="w-4 h-4" /> Профиль
              </router-link>
              <router-link to="/about" @click="mobileOpen = false" class="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium text-primary-200 hover:text-white hover:bg-white/10 transition-all active:scale-[0.97]">
                <TicketIcon class="w-4 h-4" /> О проекте
              </router-link>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- Mobile overlay backdrop -->
    <Transition name="overlay">
      <div
        v-if="mobileOpen"
        class="md:hidden fixed inset-0 bg-black/40 z-[-1]"
        @click="mobileOpen = false"
      />
    </Transition>
  </header>
</template>

<style scoped>
.dropdown-enter-active, .dropdown-leave-active { transition: all 0.2s ease; }
.dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(-8px); }

/* === Mobile menu smooth slide === */
.mobile-menu-enter-active,
.mobile-menu-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 500px;
  opacity: 1;
}
.mobile-menu-enter-active .mobile-menu-content,
.mobile-menu-leave-active .mobile-menu-content {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.mobile-menu-enter-from,
.mobile-menu-leave-to {
  max-height: 0;
  opacity: 0;
  border-top-width: 0 !important;
}
.mobile-menu-enter-from .mobile-menu-content,
.mobile-menu-leave-to .mobile-menu-content {
  transform: translateY(-8px);
  opacity: 0;
}
.mobile-menu-enter-to .mobile-menu-content,
.mobile-menu-leave-from .mobile-menu-content {
  transform: translateY(0);
  opacity: 1;
}

/* === Burger icon rotation === */
.burger-icon-enter-active,
.burger-icon-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.burger-icon-enter-from {
  opacity: 0;
  transform: rotate(-90deg) scale(0.7);
}
.burger-icon-leave-to {
  opacity: 0;
  transform: rotate(90deg) scale(0.7);
}
.burger-icon-leave-active {
  position: absolute;
}

/* === Backdrop overlay === */
.overlay-enter-active,
.overlay-leave-active {
  transition: opacity 0.3s ease;
}
.overlay-enter-from,
.overlay-leave-to {
  opacity: 0;
}
</style>
