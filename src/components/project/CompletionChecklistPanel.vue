<script setup lang="ts">
import { CheckCircle2, Circle } from '@lucide/vue'

import type { ProjectCompletionChecklist } from '@/types/ProjectCompletion'

defineProps<{
  checklist: ProjectCompletionChecklist
}>()

const ITEMS: { key: keyof ProjectCompletionChecklist; label: string }[] = [
  { key: 'contract', label: 'Contract' },
  { key: 'payments', label: 'Payments' },
  { key: 'design', label: 'Design Approval' },
  { key: 'governmentApproval', label: 'Government Approval' },
  { key: 'fieldWork', label: 'Field Work' },
]
</script>

<template>
  <div>
    <p class="mb-2 text-xs text-text-muted">Completion Checklist</p>
    <ul class="flex flex-col gap-2">
      <li
        v-for="item in ITEMS"
        :key="item.key"
        class="flex items-center gap-2.5 rounded-lg border p-2.5"
        :class="checklist[item.key].complete ? 'border-success-200 bg-success-50' : 'border-border-light bg-bg-card'"
      >
        <CheckCircle2 v-if="checklist[item.key].complete" class="h-4 w-4 shrink-0 text-success-600" aria-hidden="true" />
        <Circle v-else class="h-4 w-4 shrink-0 text-text-muted" aria-hidden="true" />
        <div class="min-w-0 flex-1">
          <p class="text-sm font-medium text-text-primary">{{ item.label }}</p>
          <p class="text-xs text-text-muted">{{ checklist[item.key].detail }}</p>
        </div>
      </li>
    </ul>
  </div>
</template>
