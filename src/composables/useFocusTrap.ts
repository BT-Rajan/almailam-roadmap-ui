import { nextTick, onBeforeUnmount, watch, type Ref } from 'vue'

const FOCUSABLE_SELECTOR = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(', ')

interface FocusTrapOptions {
  // Defaults to focusing the container itself (must carry tabindex="-1" in
  // the template). Landing focus on "first focusable descendant" instead
  // would put it on whatever happens to render first -- often just a close
  // button -- so callers that want something specific (CommandPalette's
  // search input) opt in explicitly instead.
  initialFocus?: () => HTMLElement | null | undefined
}

/**
 * Traps Tab/Shift+Tab within `containerRef` while `isActive()` is true,
 * moves focus in on activation, and restores it to whatever was focused
 * before on deactivation. Used by BaseDialog/BaseDrawer/CommandPalette so
 * every consumer gets correct modal focus behavior for free.
 */
export function useFocusTrap(
  containerRef: Ref<HTMLElement | undefined>,
  isActive: () => boolean,
  options: FocusTrapOptions = {},
): void {
  let previouslyFocused: HTMLElement | null = null

  function getFocusable(): HTMLElement[] {
    if (!containerRef.value) return []
    return Array.from(containerRef.value.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR))
  }

  function focusInitial(): void {
    const explicit = options.initialFocus?.()
    if (explicit) {
      explicit.focus()
      return
    }
    containerRef.value?.focus()
  }

  function handleKeydown(event: KeyboardEvent): void {
    if (event.key !== 'Tab' || !containerRef.value) return

    const focusable = getFocusable()
    if (focusable.length === 0) {
      event.preventDefault()
      return
    }

    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    const current = document.activeElement as HTMLElement | null
    const currentIsInside = current !== null && containerRef.value.contains(current)

    if (event.shiftKey) {
      if (!currentIsInside || current === first) {
        event.preventDefault()
        last.focus()
      }
    } else if (!currentIsInside || current === last) {
      event.preventDefault()
      first.focus()
    }
  }

  watch(
    isActive,
    (active) => {
      if (active) {
        previouslyFocused = document.activeElement as HTMLElement | null
        document.addEventListener('keydown', handleKeydown, true)
        // Teleported/v-if content isn't in the DOM yet when this watcher
        // runs -- containerRef.value is still last render's value until
        // after the pending patch flushes.
        void nextTick(focusInitial)
      } else {
        document.removeEventListener('keydown', handleKeydown, true)
        if (previouslyFocused && document.body.contains(previouslyFocused)) {
          previouslyFocused.focus()
        }
        previouslyFocused = null
      }
    },
    { immediate: true },
  )

  onBeforeUnmount(() => {
    document.removeEventListener('keydown', handleKeydown, true)
  })
}
