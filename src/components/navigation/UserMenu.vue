<script setup lang="ts">
import { KeyRound, LogOut, Moon, Sun, User, UserCircle } from '@lucide/vue'
import { onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'

import ChangePasswordDialog from '@/components/navigation/ChangePasswordDialog.vue'
import ProfileDialog from '@/components/navigation/ProfileDialog.vue'
import { useAuth } from '@/composables/useAuthComposable'
import { useOverlayStack } from '@/composables/useOverlayStack'
import { useTheme } from '@/composables/useTheme'
import { ROUTE_NAMES } from '@/constants/routeNames'

const router = useRouter()
const { username, logout } = useAuth()
const { isDark, toggleMode } = useTheme()

const isOpen = ref(false)
const isProfileOpen = ref(false)
const isChangePasswordOpen = ref(false)
const menuRef = ref<HTMLElement>()
const triggerRef = ref<HTMLButtonElement>()

// Opens on hover, so it can be "open" purely because the pointer is resting
// near the avatar -- registered as non-blocking so it never silently stops
// Ctrl+K (see useOverlayStack) from working. It still takes part in the
// shared stack for Escape/topmost purposes.
const { isTopmost } = useOverlayStack(() => isOpen.value, { blocking: false })

// Hover-intent close: leaving the trigger for the panel (or vice versa) is
// a brief gap, so closing immediately on mouseleave would make the menu
// feel like it snaps shut before the pointer arrives. The short delay is
// cancelled by the next mouseenter within the same container.
let closeTimeout: ReturnType<typeof setTimeout> | undefined

function openOnHover(): void {
  clearTimeout(closeTimeout)
  isOpen.value = true
}

function closeOnHover(): void {
  clearTimeout(closeTimeout)
  closeTimeout = setTimeout(() => {
    isOpen.value = false
  }, 150)
}

function toggleOpen(): void {
  clearTimeout(closeTimeout)
  isOpen.value = !isOpen.value
}

function close(): void {
  clearTimeout(closeTimeout)
  isOpen.value = false
}

function handleClickOutside(event: MouseEvent): void {
  if (isOpen.value && isTopmost() && menuRef.value && !menuRef.value.contains(event.target as Node)) {
    close()
  }
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape' && isOpen.value && isTopmost()) {
    close()
    // Keyboard-driven close should hand focus back to the trigger so a
    // keyboard user doesn't lose their place. Pointer-driven closes
    // (hover-out, click-outside, menu-item clicks) deliberately don't do
    // this -- it would fight focus the user didn't ask for (a click on
    // "My Profile" should land focus in the dialog that opens, not back on
    // this button).
    triggerRef.value?.focus()
  }
}

window.addEventListener('mousedown', handleClickOutside)
window.addEventListener('keydown', handleKeydown)
onBeforeUnmount(() => {
  clearTimeout(closeTimeout)
  window.removeEventListener('mousedown', handleClickOutside)
  window.removeEventListener('keydown', handleKeydown)
})

function openProfile(): void {
  close()
  isProfileOpen.value = true
}

function openChangePassword(): void {
  close()
  isChangePasswordOpen.value = true
}

async function handleLogout(): Promise<void> {
  close()
  await logout()
  router.push({ name: ROUTE_NAMES.LOGIN })
}
</script>

<template>
  <div ref="menuRef" class="relative" @mouseenter="openOnHover" @mouseleave="closeOnHover">
    <button
      ref="triggerRef"
      type="button"
      class="flex items-center gap-2 rounded-lg py-1.5 pl-1.5 pr-3 text-sm font-medium text-[var(--color-text-primary)] transition-colors duration-fast hover:bg-[var(--color-bg-hover)]"
      aria-haspopup="menu"
      :aria-expanded="isOpen"
      @click="toggleOpen"
    >
      <span class="gradient-luxe-accent flex h-7 w-7 items-center justify-center rounded-full text-white">
        <User :size="16" />
      </span>
      <span class="hidden sm:inline">{{ username }}</span>
    </button>

    <Transition name="menu-fade">
      <div
        v-if="isOpen"
        role="menu"
        class="glass-panel absolute right-0 top-full z-dropdown mt-1 w-56 rounded-xl border border-border-light py-1.5 shadow-elevated"
      >
        <button
          type="button"
          role="menuitem"
          class="flex w-full items-center gap-2.5 px-3.5 py-2 text-left text-sm text-text-primary transition-colors duration-fast hover:bg-bg-hover"
          @click="openProfile"
        >
          <UserCircle :size="16" class="text-text-muted" />
          <span>My Profile</span>
        </button>

        <button
          type="button"
          role="menuitem"
          class="flex w-full items-center gap-2.5 px-3.5 py-2 text-left text-sm text-text-primary transition-colors duration-fast hover:bg-bg-hover"
          @click="toggleMode"
        >
          <component :is="isDark ? Sun : Moon" :size="16" class="text-text-muted" />
          <span>{{ isDark ? 'Light Mode' : 'Dark Mode' }}</span>
        </button>

        <button
          type="button"
          role="menuitem"
          class="flex w-full items-center gap-2.5 px-3.5 py-2 text-left text-sm text-text-primary transition-colors duration-fast hover:bg-bg-hover"
          @click="openChangePassword"
        >
          <KeyRound :size="16" class="text-text-muted" />
          <span>Change Password</span>
        </button>

        <hr class="my-1.5 border-border-light" />

        <button
          type="button"
          role="menuitem"
          class="flex w-full items-center gap-2.5 px-3.5 py-2 text-left text-sm text-danger-500 transition-colors duration-fast hover:bg-danger-50"
          @click="handleLogout"
        >
          <LogOut :size="16" />
          <span>Logout</span>
        </button>
      </div>
    </Transition>
  </div>

  <ProfileDialog v-model="isProfileOpen" />
  <ChangePasswordDialog v-model="isChangePasswordOpen" />
</template>

<style scoped>
.menu-fade-enter-active,
.menu-fade-leave-active {
  transition:
    opacity 120ms ease,
    transform 120ms ease;
}
.menu-fade-enter-from,
.menu-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
