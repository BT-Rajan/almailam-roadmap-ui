import { computed, onMounted, onUnmounted, ref } from 'vue'

// Mirrors tailwind.config.js's `tablet` breakpoint (768px) -- the single
// source of truth for where the app stops being usable. Below this width
// the layout has nowhere left to collapse to (sidebar, tables, multi-column
// forms all assume at least a tablet-sized canvas), so rather than let
// every page silently break in its own way, App.vue gates the whole shell
// behind MobileBlockScreen.vue using this same number.
const MOBILE_BREAKPOINT_PX = 768

const width = ref(typeof window !== 'undefined' ? window.innerWidth : MOBILE_BREAKPOINT_PX)
let listenerCount = 0

function handleResize() {
  width.value = window.innerWidth
}

/**
 * App-wide reactive viewport width, backed by a single shared resize
 * listener (ref-counted across every component that calls this) rather
 * than one `addEventListener('resize', ...)` per consumer.
 */
export function useViewport() {
  onMounted(() => {
    if (listenerCount === 0) {
      window.addEventListener('resize', handleResize)
    }
    listenerCount += 1
    handleResize()
  })

  onUnmounted(() => {
    listenerCount -= 1
    if (listenerCount === 0) {
      window.removeEventListener('resize', handleResize)
    }
  })

  return {
    width,
    isBelowTablet: computed(() => width.value < MOBILE_BREAKPOINT_PX),
  }
}

export { MOBILE_BREAKPOINT_PX }
