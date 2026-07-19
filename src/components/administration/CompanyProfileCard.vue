<script setup lang="ts">
import { Globe, Mail, MapPin, Phone } from '@lucide/vue'

import Avatar from '@/components/common/Avatar.vue'
import Card from '@/components/common/Card.vue'
import type { CompanySettings } from '@/types/CompanySettings'

defineProps<{
  settings: CompanySettings
}>()
</script>

<template>
  <Card>
    <div class="flex flex-col gap-4">
      <div class="flex items-center gap-3">
        <Avatar :name="settings.companyName" size="lg" />
        <div class="min-w-0">
          <p class="truncate font-semibold text-neutral-900">{{ settings.companyName }}</p>
          <p class="truncate text-sm text-neutral-500">{{ settings.tagline }}</p>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <span class="text-xs font-medium text-neutral-500">Brand Color</span>
        <span class="h-5 w-5 rounded-full border border-border-light" :style="{ backgroundColor: settings.brandColor }" />
        <span class="text-xs text-neutral-500">{{ settings.brandColor }}</span>
      </div>

      <div class="flex flex-col gap-2 border-t border-border-light pt-4 text-sm text-neutral-600">
        <div class="flex items-center gap-2">
          <MapPin class="h-4 w-4 shrink-0 text-neutral-400" />
          <span>{{ settings.address }}, {{ settings.city }}, {{ settings.country }}</span>
        </div>
        <div class="flex items-center gap-2">
          <Phone class="h-4 w-4 shrink-0 text-neutral-400" />
          <span>{{ settings.phone }}</span>
        </div>
        <div class="flex items-center gap-2">
          <Mail class="h-4 w-4 shrink-0 text-neutral-400" />
          <span>{{ settings.email }}</span>
        </div>
        <div class="flex items-center gap-2">
          <Globe class="h-4 w-4 shrink-0 text-neutral-400" />
          <span>{{ settings.website }}</span>
        </div>
      </div>
    </div>
  </Card>
</template>
