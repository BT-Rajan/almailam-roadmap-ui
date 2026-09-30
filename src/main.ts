import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import { i18n } from './i18n'
import router from './router'
import { useLocaleStore } from './stores/localeStore'
import { installSessionBootstrap } from './stores/sessionBootstrap'
import { useThemeStore } from './stores/themeStore'
import { isChunkLoadError, reloadForNewBuild } from './utils/chunkReload'

import './styles/main.css'

const app = createApp(App)

// A page or tab chunk that no longer exists after a deploy (see
// utils/chunkReload.ts) used to leave a blank page. Three places can see it:
// a route's lazy page, Vite's preload of a chunk's dependencies, and a
// lazily loaded component inside an already-open page.
router.onError((error, to) => {
  if (isChunkLoadError(error)) reloadForNewBuild(router.resolve(to).href)
})
window.addEventListener('vite:preloadError', (event) => {
  if (reloadForNewBuild()) event.preventDefault()
})
app.config.errorHandler = (error, _instance, info) => {
  if (isChunkLoadError(error) && reloadForNewBuild()) return
  console.error(error, info)
}

app.use(createPinia())
installSessionBootstrap()
app.use(router)
app.use(i18n)

useThemeStore().initializeTheme()
// Started now so the locale's messages download alongside the router's
// initial navigation rather than after it.
const localeReady = useLocaleStore().initializeLocale()

// Wait for the router's initial navigation (including the beforeEach guard's
// auth redirect, e.g. '/' -> '/login') to resolve before mounting. Mounting
// immediately would render App.vue against the unmatched "start location"
// for one tick, whose route.meta is empty -- see App.vue's layout fallback.
// Also wait for the locale's messages, so an Arabic user never sees English
// (the fallback) flash up first. initializeLocale never rejects.
// allSettled, not all: if the first navigation fails (e.g. its page chunk
// can't load), the app still mounts instead of leaving a permanently blank
// page with nothing to click.
void Promise.allSettled([router.isReady(), localeReady]).then(() => {
  app.mount('#app')
})
