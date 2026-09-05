import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import { i18n } from './i18n'
import router from './router'
import { useLocaleStore } from './stores/localeStore'
import { useThemeStore } from './stores/themeStore'

import './styles/main.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(i18n)

useThemeStore().initializeTheme()
useLocaleStore().initializeLocale()

// Wait for the router's initial navigation (including the beforeEach guard's
// auth redirect, e.g. '/' -> '/login') to resolve before mounting. Mounting
// immediately would render App.vue against the unmatched "start location"
// for one tick, whose route.meta is empty -- see App.vue's layout fallback.
router.isReady().then(() => {
  app.mount('#app')
})
