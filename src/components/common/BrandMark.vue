<script setup lang="ts">
import { ref, watch } from 'vue'
import { PUBLIC_LOGO_URL } from '@/services/companyService'
import { useCompanyStore } from '@/stores/companyStore'

// The app's logo mark, shared by every shell that used to hardcode its
// own "SO" gradient badge (Sidebar, MobileSidebar, AuthLayout, the
// Customer/Site portal headers) -- now shows the company's own
// uploaded logo (Administration > Company > Branding) when there is
// one, falling back to the original badge (via the default slot)
// otherwise. companyStore.branding is loaded once at app boot
// (App.vue), fully public, so this works even on the sign-in screen.
withDefaults(defineProps<{ sizeClass?: string }>(), { sizeClass: 'h-9 w-9' })

const companyStore = useCompanyStore()

// Reset on a branding change (e.g. an admin just removed the logo, or
// swapped it for a new file at the same URL) rather than getting stuck
// on a stale failure from a previous logo.
const logoFailed = ref(false)
watch(() => companyStore.branding?.hasLogo, () => { logoFailed.value = false })
</script>

<template>
  <img
    v-if="companyStore.branding?.hasLogo && !logoFailed"
    :src="PUBLIC_LOGO_URL"
    :alt="companyStore.branding.companyName"
    :class="sizeClass"
    class="shrink-0 rounded-lg bg-white object-contain p-0.5 shadow-glass-sm"
    @error="logoFailed = true"
  />
  <div
    v-else
    :class="sizeClass"
    class="gradient-luxe-accent flex shrink-0 items-center justify-center rounded-lg text-sm font-semibold text-white shadow-glass-sm"
  >
    <slot>SO</slot>
  </div>
</template>
