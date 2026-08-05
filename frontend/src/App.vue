<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'
import ToastContainer from '@/components/ToastContainer.vue'

const route = useRoute()
const auth = useAuthStore()

// Theme: auto-detect system preference, override with explicit user choice
const storedTheme = localStorage.getItem('theme')
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)')
const userChose = storedTheme === 'dark' || storedTheme === 'light'

const dark = ref(
  userChose ? storedTheme === 'dark' : prefersDark.matches
)

const applyTheme = () => {
  if (dark.value) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}
applyTheme()

// Listen to system theme changes unless user has explicitly chosen
const onSystemThemeChange = (e: MediaQueryListEvent) => {
  if (!userChose) {
    dark.value = e.matches
  }
}
prefersDark.addEventListener('change', onSystemThemeChange)

watch(dark, () => {
  applyTheme()
  localStorage.setItem('theme', dark.value ? 'dark' : 'light')
})

const toggleDark = () => { dark.value = !dark.value }

const noHeaderRoutes = ['/login', '/register', '/forgot-password', '/reset-password', '/verify-email']
const showHeader = () => !noHeaderRoutes.includes(route.path)

onMounted(() => {
  if (auth.token && !auth.user) {
    auth.fetchMe()
  }
})

onUnmounted(() => {
  prefersDark.removeEventListener('change', onSystemThemeChange)
})
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <AppHeader v-if="showHeader()" :dark="dark" @toggle-dark="toggleDark" />
    <main class="flex-1">
      <router-view v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </router-view>
    </main>
    <AppFooter v-if="showHeader()" />
    <ToastContainer />
  </div>
</template>
