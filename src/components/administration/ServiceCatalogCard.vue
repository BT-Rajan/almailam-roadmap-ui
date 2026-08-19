<script setup lang="ts">
import { ListChecks } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
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
        <p class="truncate font-medium text-neutral-900">{{ service.name }}</p>
        <p class="mt-1 text-sm text-neutral-500">{{ service.activities.length }} activities</p>
      </div>
    </div>
  </Card>
</template>
