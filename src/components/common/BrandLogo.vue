<script setup lang="ts">
import { Compass } from '@lucide/vue'
import { onMounted, onUnmounted, ref } from 'vue'

import { companyService } from '@/services/companyService'

// Renders the admin-uploaded company logo (Administration > Company >
// Branding) wherever the app needs its brand mark -- the sidebar, the
// sign-in screen, and the customer/site-engineer portal headers -- always
// paired by the caller with the company name text next to it, so together
// they read as the full logo + name wordmark regardless of whether the
// uploaded image itself is icon-only or already a combined lockup.
//
// Falls back to a generic mark until a logo is uploaded, fetched through
// the unauthenticated /logo/public endpoint (see companyService.
// getPublicLogoBlob) since this renders before login and for roles with
// no Administration permission alike.
withDefaults(
  defineProps<{
    size?: 'sm' | 'md' | 'lg'
  }>(),
  { size: 'md' },
)

const logoUrl = ref<string | undefined>(undefined)
const hasLogo = ref(false)

onMounted(async () => {
  try {
    const blob = await companyService.getPublicLogoBlob()
    logoUrl.value = URL.createObjectURL(blob)
    hasLogo.value = true
  } catch {
    hasLogo.value = false
  }
})

onUnmounted(() => {
  if (logoUrl.value) URL.revokeObjectURL(logoUrl.value)
})

const BOX_SIZE_CLASSES = { sm: 'h-7 w-7', md: 'h-9 w-9', lg: 'h-12 w-12' } as const
const IMG_HEIGHT_CLASSES = { sm: 'h-7', md: 'h-9', lg: 'h-12' } as const
const ICON_SIZES = { sm: 14, md: 16, lg: 22 } as const
</script>

<template>
  <img
    v-if="hasLogo"
    :src="logoUrl"
    alt=""
    class="w-auto max-w-[8rem] shrink-0 object-contain"
    :class="IMG_HEIGHT_CLASSES[size]"
  />
  <div
    v-else
    class="gradient-luxe-accent flex shrink-0 items-center justify-center rounded-lg text-white shadow-glass-sm"
    :class="BOX_SIZE_CLASSES[size]"
  >
    <Compass :size="ICON_SIZES[size]" :stroke-width="1.75" />
  </div>
</template>
