import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useThemeStore } from './stores/themeStore'

import './styles/main.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

useThemeStore().initializeTheme()

// Wait for the router's initial navigation (including the beforeEach guard's
// auth redirect, e.g. '/' -> '/login') to resolve before mounting. Mounting
// immediately would render App.vue against the unmatched "start location"
// for one tick, whose route.meta is empty -- see App.vue's layout fallback.
router.isReady().then(() => {
  app.mount('#app')
})
