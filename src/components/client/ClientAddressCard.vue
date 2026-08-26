<script setup lang="ts">
import { MapPin, Pencil, Trash2 } from '@lucide/vue'
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import IconButton from '@/components/common/IconButton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ClientAddress } from '@/types/Client'

const props = defineProps<{
  address: ClientAddress
}>()

defineEmits<{
  edit: []
  delete: []
}>()

const addressLine = computed(() =>
  [props.address.building, props.address.street, props.address.area, props.address.city, props.address.state, props.address.country]
    .filter(Boolean)
    .join(', '),
)
</script>

<template>
  <Card>
    <div class="flex items-start justify-between gap-3">
      <div class="flex items-start gap-3">
        <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-info-50 text-info-600">
          <MapPin class="h-4 w-4" />
        </span>
        <div class="flex flex-col gap-1">
          <StatusBadge :label="address.addressType" variant="info" size="sm" />
          <p class="text-sm text-text-secondary">{{ addressLine }}</p>
        </div>
      </div>
      <div class="flex shrink-0 items-center gap-1">
        <IconButton :icon="Pencil" :label="`Edit ${address.addressType} address`" size="sm" @click="$emit('edit')" />
        <IconButton :icon="Trash2" :label="`Remove ${address.addressType} address`" size="sm" variant="danger" @click="$emit('delete')" />
      </div>
    </div>
  </Card>
</template>
