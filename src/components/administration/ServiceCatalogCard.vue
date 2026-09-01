<script setup lang="ts">
import { ListChecks } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ServiceCatalogItem } from '@/types/ServiceCatalog'

defineProps<{
  service: ServiceCatalogItem
  active: boolean
}>()

defineEmits<{
  select: [serviceId: string]
}>()
</script>

<template>
  <Card
    hoverable
    class="cursor-pointer"
    :class="active ? 'border-primary-400 ring-1 ring-primary-400' : ''"
    @click="$emit('select', service.id)"
  >
    <div class="flex items-start gap-3">
      <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-50">
        <ListChecks class="h-4 w-4 text-primary-600" />
      </span>
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2">
          <p class="text-sm font-semibold text-text-primary truncate">{{ service.name }}</p>
          <StatusBadge :label="service.branch" :variant="service.branch === 'Supervision' ? 'info' : 'neutral'" />
        </div>
        <p class="mt-1 text-sm text-text-muted">
          {{ service.activities.length }} activit{{ service.activities.length === 1 ? 'y' : 'ies' }}
          <span v-if="service.branch === 'Supervision'">(monthly)</span>
        </p>
      </div>
    </div>
  </Card>
</template>
