<script setup lang="ts">
import { MapPin } from '@lucide/vue'
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ClientAddress } from '@/types/Client'

const props = defineProps<{
  address: ClientAddress
}>()

const addressLine = computed(() =>
  [props.address.building, props.address.street, props.address.area, props.address.city, props.address.state, props.address.country]
    .filter(Boolean)
    .join(', '),
)
</script>

<template>
  <Card>
    <div class="flex items-start gap-3">
      <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-info-50 text-info-600">
        <MapPin class="h-4 w-4" />
      </span>
      <div class="flex flex-col gap-1">
        <StatusBadge :label="address.addressType" variant="info" size="sm" />
        <p class="text-sm text-neutral-700">{{ addressLine }}</p>
      </div>
    </div>
  </Card>
</template>
