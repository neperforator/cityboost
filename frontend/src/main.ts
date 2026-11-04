import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import './style.css'

const app = createApp(App)

// Sentry (продакшен) — установить @sentry/vue и @sentry/browser для включения
// if (import.meta.env.PROD && import.meta.env.VITE_SENTRY_DSN) { ... }

const pinia = createPinia()
app.use(pinia)

const auth = useAuthStore(pinia)

// Access-токен живёт только в памяти, поэтому на старте восстанавливаем сессию
// по httpOnly refresh-cookie до первой навигации.
auth.bootstrap().finally(() => {
  app.use(router)
  app.mount('#app')
})
