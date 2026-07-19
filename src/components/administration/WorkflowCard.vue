<script setup lang="ts">
import { Workflow } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { WorkflowTemplate } from '@/types/Workflow'

defineProps<{
  template: WorkflowTemplate
  active: boolean
}>()

defineEmits<{
  select: [templateId: string]
}>()
</script>

<template>
  <Card
    hoverable
    class="cursor-pointer"
    :class="active ? 'border-primary-400 ring-1 ring-primary-400' : ''"
    @click="$emit('select', template.id)"
  >
    <div class="flex items-start gap-3">
      <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-50">
        <Workflow class="h-4 w-4 text-primary-600" />
      </span>
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2">
          <p class="truncate font-medium text-neutral-900">{{ template.name }}</p>
          <StatusBadge v-if="template.isDefault" label="Default" variant="success" size="sm" />
        </div>
        <p class="mt-1 text-sm text-neutral-500">{{ template.stages.length }} stages</p>
      </div>
    </div>
  </Card>
</template>
