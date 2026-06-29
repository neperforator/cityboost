import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)

// Sentry (продакшен) — установить @sentry/vue и @sentry/browser для включения
// if (import.meta.env.PROD && import.meta.env.VITE_SENTRY_DSN) { ... }

app.use(createPinia())
app.use(router)
app.mount('#app')
