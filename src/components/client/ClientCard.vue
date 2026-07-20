<script setup lang="ts">
import { Mail, MapPin, Phone } from '@lucide/vue'
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { Client } from '@/types/Client'
import { getClientDisplayName, getClientOnboardingStateVariant, getClientStatusVariant } from '@/utils/clientHelpers'

const props = defineProps<{
  client: Client
}>()

defineEmits<{
  open: [clientId: string]
}>()

const displayName = computed(() => getClientDisplayName(props.client))
</script>

<template>
  <Card hoverable class="cursor-pointer" @click="$emit('open', client.id)">
    <div class="flex flex-col gap-4">
      <div class="flex items-start justify-between gap-3">
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">{{ client.code }} · {{ client.clientType }}</p>
          <h3 class="text-base font-semibold leading-snug text-neutral-800">{{ displayName }}</h3>
        </div>
        <StatusBadge :label="client.status" :variant="getClientStatusVariant(client.status)" show-dot />
      </div>

      <div class="flex flex-col gap-1.5 text-sm text-neutral-500">
        <div class="flex items-center gap-2">
          <Phone class="h-4 w-4 shrink-0 text-neutral-400" />
          <span class="truncate">{{ client.mobile }}</span>
        </div>
        <div class="flex items-center gap-2">
          <Mail class="h-4 w-4 shrink-0 text-neutral-400" />
          <span class="truncate">{{ client.email }}</span>
        </div>
        <div class="flex items-center gap-2">
          <MapPin class="h-4 w-4 shrink-0 text-neutral-400" />
          <span class="truncate">{{ client.city }}</span>
        </div>
      </div>

      <div class="flex items-center justify-between border-t border-border-light pt-3">
        <StatusBadge :label="client.onboardingState" :variant="getClientOnboardingStateVariant(client.onboardingState)" size="sm" />
      </div>
    </div>
  </Card>
</template>
