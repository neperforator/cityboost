<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  Bars3Icon, XMarkIcon, SunIcon, MoonIcon, ClipboardDocumentListIcon,
  UserCircleIcon, ArrowRightOnRectangleIcon, UsersIcon,
  ClockIcon, PlusIcon, InformationCircleIcon,
} from '@heroicons/vue/24/outline'

defineProps({ dark: Boolean })
defineEmits(['toggleDark'])

const auth = useAuthStore()
const router = useRouter()
const mobileOpen = ref(false)

const initials = computed(() => {
  if (!auth.userName) return '?'
  return auth.userName.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
})

const activeRoute = computed(() => router.currentRoute.value.path)

const adminLinks = [
  { to: '/admin', label: 'Все заявки', icon: ClipboardDocumentListIcon },
  { to: '/admin/users', label: 'Пользователи', icon: UsersIcon },
  { to: '/admin/audit', label: 'Аудит-лог', icon: ClockIcon },
]

function go(to: string) {
  router.push(to)
  mobileOpen.value = false
}

watch(mobileOpen, (val) => {
  if (window.innerWidth < 768) {
    document.documentElement.classList.toggle('overflow-hidden', val)
  }
})
</script>

<template>
  <!-- Desktop route rail -->
  <aside class="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r-2 border-line bg-surface dark:border-line-dark dark:bg-surface-dark md:flex">
    <div class="border-b-2 border-line px-5 py-6 dark:border-line-dark">
      <router-link to="/dashboard" class="block">
        <span class="font-display text-xl font-semibold tracking-tight text-ink dark:text-ink-dark">CityBoost</span>
        <span class="mt-1 block text-xs font-medium text-ink-soft dark:text-ink-dark-soft">Городская служба заявок</span>
      </router-link>
    </div>

    <nav class="flex-1 overflow-y-auto px-3 py-5">
      <p class="px-3 pb-2 text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">Работа с заявками</p>
      <router-link
        to="/dashboard"
        class="nav-item"
        :class="{ 'nav-item-active': activeRoute === '/dashboard' }"
      >
        <ClipboardDocumentListIcon class="h-4 w-4" />
        Мои заявки
      </router-link>
      <router-link to="/tickets/create" class="btn-accent mt-3 w-full">
        <PlusIcon class="h-4 w-4" />
        Новая заявка
      </router-link>
      <router-link
        to="/profile"
        class="nav-item mt-1"
        :class="{ 'nav-item-active': activeRoute === '/profile' }"
      >
        <UserCircleIcon class="h-4 w-4" />
        Профиль
      </router-link>
      <router-link
        to="/about"
        class="nav-item"
        :class="{ 'nav-item-active': activeRoute === '/about' }"
      >
        <InformationCircleIcon class="h-4 w-4" />
        О проекте
      </router-link>

      <template v-if="auth.isAdmin">
        <div class="my-5 border-t-2 border-line dark:border-line-dark" />
        <p class="px-3 pb-2 text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">Админ-панель</p>
        <router-link
          v-for="link in adminLinks"
          :key="link.to"
          :to="link.to"
          class="nav-item"
          :class="{ 'nav-item-active': activeRoute === link.to || (link.to === '/admin' && activeRoute.startsWith('/admin/tickets')) }"
        >
          <component :is="link.icon" class="h-4 w-4" />
          {{ link.label }}
        </router-link>
      </template>
    </nav>

    <div class="border-t-2 border-line p-3 dark:border-line-dark">
      <router-link to="/profile" class="flex items-center gap-3 rounded-sm px-2 py-2 hover:bg-black/5 dark:hover:bg-white/5">
        <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-sm bg-primary-500 text-xs font-bold text-white">{{ initials }}</span>
        <span class="min-w-0">
          <span class="block truncate text-sm font-medium text-ink dark:text-ink-dark">{{ auth.userName }}</span>
          <span class="block truncate text-xs text-ink-soft dark:text-ink-dark-soft">{{ auth.userEmail }}</span>
        </span>
      </router-link>
      <div class="mt-2 flex gap-2">
        <button
          @click="$emit('toggleDark')"
          class="btn-ghost btn-sm flex-1"
          :aria-label="dark ? 'Светлая тема' : 'Тёмная тема'"
        >
          <SunIcon v-if="dark" class="h-4 w-4" />
          <MoonIcon v-else class="h-4 w-4" />
          {{ dark ? 'Светлая' : 'Тёмная' }}
        </button>
        <button @click="auth.logout()" class="btn-ghost btn-sm" aria-label="Выйти">
          <ArrowRightOnRectangleIcon class="h-4 w-4" />
        </button>
      </div>
    </div>
  </aside>

  <!-- Mobile top bar -->
  <header class="sticky top-0 z-40 flex h-16 items-center justify-between border-b-2 border-line bg-surface px-4 dark:border-line-dark dark:bg-surface-dark md:hidden">
    <router-link to="/dashboard" class="flex items-center gap-2">
      <span class="flex h-8 w-8 items-center justify-center rounded-sm bg-primary-500 text-[10px] font-bold text-white">CB</span>
      <span class="font-display text-base font-semibold text-ink dark:text-ink-dark">CityBoost</span>
    </router-link>
    <div class="flex items-center gap-1">
      <router-link to="/tickets/create" class="btn-accent btn-sm" aria-label="Новая заявка">
        <PlusIcon class="h-4 w-4" />
      </router-link>
      <button @click="$emit('toggleDark')" class="btn-ghost btn-sm" :aria-label="dark ? 'Светлая тема' : 'Тёмная тема'">
        <SunIcon v-if="dark" class="h-4 w-4" />
        <MoonIcon v-else class="h-4 w-4" />
      </button>
      <button
        @click="mobileOpen = !mobileOpen"
        class="btn-ghost btn-sm"
        :aria-label="mobileOpen ? 'Закрыть меню' : 'Открыть меню'"
        :aria-expanded="mobileOpen"
      >
        <XMarkIcon v-if="mobileOpen" class="h-5 w-5" />
        <Bars3Icon v-else class="h-5 w-5" />
      </button>
    </div>
  </header>

  <!-- Mobile drawer -->
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="mobileOpen" class="fixed inset-0 z-50 md:hidden">
        <div class="absolute inset-0 bg-ink/50 dark:bg-black/70" @click="mobileOpen = false" />
        <div class="absolute right-0 top-0 flex h-full w-80 max-w-[86vw] flex-col border-l-2 border-line bg-surface dark:border-line-dark dark:bg-surface-dark">
          <div class="flex items-center justify-between border-b-2 border-line px-5 py-4 dark:border-line-dark">
            <span class="font-display text-base font-semibold text-ink dark:text-ink-dark">Меню</span>
            <button @click="mobileOpen = false" class="btn-ghost btn-sm" aria-label="Закрыть меню">
              <XMarkIcon class="h-5 w-5" />
            </button>
          </div>
          <nav class="flex-1 overflow-y-auto p-3">
            <button @click="go('/dashboard')" class="nav-item w-full" :class="{ 'nav-item-active': activeRoute === '/dashboard' }">
              <ClipboardDocumentListIcon class="h-4 w-4" /> Мои заявки
            </button>
            <button @click="go('/tickets/create')" class="nav-item w-full">
              <PlusIcon class="h-4 w-4" /> Новая заявка
            </button>
            <button @click="go('/profile')" class="nav-item w-full" :class="{ 'nav-item-active': activeRoute === '/profile' }">
              <UserCircleIcon class="h-4 w-4" /> Профиль
            </button>
            <button @click="go('/about')" class="nav-item w-full" :class="{ 'nav-item-active': activeRoute === '/about' }">
              <InformationCircleIcon class="h-4 w-4" /> О проекте
            </button>

            <template v-if="auth.isAdmin">
              <div class="my-4 border-t-2 border-line dark:border-line-dark" />
              <p class="px-3 pb-2 text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">Админ-панель</p>
              <button
                v-for="link in adminLinks"
                :key="link.to"
                @click="go(link.to)"
                class="nav-item w-full"
                :class="{ 'nav-item-active': activeRoute === link.to }"
              >
                <component :is="link.icon" class="h-4 w-4" />
                {{ link.label }}
              </button>
            </template>
          </nav>
          <div class="border-t-2 border-line p-4 dark:border-line-dark">
            <div class="flex items-center gap-3">
              <span class="flex h-9 w-9 items-center justify-center rounded-sm bg-primary-500 text-xs font-bold text-white">{{ initials }}</span>
              <div class="min-w-0">
                <p class="truncate text-sm font-medium text-ink dark:text-ink-dark">{{ auth.userName }}</p>
                <p class="truncate text-xs text-ink-soft dark:text-ink-dark-soft">{{ auth.userEmail }}</p>
              </div>
            </div>
            <button @click="auth.logout()" class="btn-secondary mt-3 w-full">
              <ArrowRightOnRectangleIcon class="h-4 w-4" />
              Выйти
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.2s ease;
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
</style>
