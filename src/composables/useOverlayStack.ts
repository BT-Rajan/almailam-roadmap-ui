import { onBeforeUnmount, watch } from 'vue'

// Module-level, not Pinia -- this is ephemeral "who's on top right now"
// coordination between overlay UI (dialogs, drawers, the command palette,
// the user menu), not application state. Shared by every instance for the
// lifetime of the page.
interface OverlayEntry {
  id: number
  // Whether this overlay should block CommandPalette's Ctrl+K from opening
  // on top of it (see isAnyOverlayOpen). UserMenu opens on hover, so it can
  // be "open" purely because the pointer is resting near the avatar --
  // that must not silently block a keyboard shortcut.
  blocking: boolean
}

let nextId = 1
const openStack: OverlayEntry[] = []

export interface OverlayHandle {
  isTopmost: () => boolean
}

export function useOverlayStack(isActive: () => boolean, options: { blocking?: boolean } = {}): OverlayHandle {
  const id = nextId++
  const blocking = options.blocking ?? true

  function register(): void {
    if (!openStack.some((entry) => entry.id === id)) {
      openStack.push({ id, blocking })
    }
  }

  function unregister(): void {
    const index = openStack.findIndex((entry) => entry.id === id)
    if (index !== -1) openStack.splice(index, 1)
  }

  watch(isActive, (active) => (active ? register() : unregister()), { immediate: true })
  onBeforeUnmount(unregister)

  return {
    isTopmost: () => openStack.length > 0 && openStack[openStack.length - 1].id === id,
  }
}

/** True if any *blocking* overlay is currently open -- used by CommandPalette's
 * Ctrl/Cmd+K handler so it doesn't pop search open on top of a modal. */
export function isAnyOverlayOpen(): boolean {
  return openStack.some((entry) => entry.blocking)
}
