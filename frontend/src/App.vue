<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'
import ToastContainer from '@/components/ToastContainer.vue'

const route = useRoute()
const auth = useAuthStore()

const storedTheme = localStorage.getItem('theme')
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)')
const userChose = storedTheme === 'dark' || storedTheme === 'light'

const dark = ref(userChose ? storedTheme === 'dark' : prefersDark.matches)

const applyTheme = () => {
  if (dark.value) document.documentElement.classList.add('dark')
  else document.documentElement.classList.remove('dark')
}
applyTheme()

const onSystemThemeChange = (e: MediaQueryListEvent) => {
  if (!userChose) dark.value = e.matches
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
  if (auth.token && !auth.user) auth.fetchMe()
})

onUnmounted(() => {
  prefersDark.removeEventListener('change', onSystemThemeChange)
})
</script>

<template>
  <div class="min-h-screen bg-canvas dark:bg-canvas-dark md:flex">
    <AppHeader v-if="showHeader()" :dark="dark" @toggle-dark="toggleDark" />
    <div class="flex min-h-screen flex-1 flex-col">
      <main class="relative flex-1">
        <router-view v-slot="{ Component }">
          <div :key="route.path" class="route-page">
            <component :is="Component" />
          </div>
        </router-view>
      </main>
      <AppFooter v-if="showHeader()" />
    </div>
    <ToastContainer />
  </div>
</template>
