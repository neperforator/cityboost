import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import 'maplibre-gl/dist/maplibre-gl.css'
import './style.css'

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)

const auth = useAuthStore(pinia)

// Access-токен живёт только в памяти, поэтому на старте восстанавливаем сессию
// по httpOnly refresh-cookie до первой навигации.
auth.bootstrap().finally(() => {
  app.use(router)
  app.mount('#app')
})
