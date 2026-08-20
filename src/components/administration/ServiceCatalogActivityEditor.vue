<script setup lang="ts">
import { Plus, Trash2 } from '@lucide/vue'
import { ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import IconButton from '@/components/common/IconButton.vue'
import TextInput from '@/components/common/TextInput.vue'
import { formatCurrency } from '@/utils/currencyFormatter'
import type { ServiceCatalogActivity } from '@/types/ServiceCatalog'

defineProps<{
  activities: ServiceCatalogActivity[]
}>()

const emit = defineEmits<{
  update: [activityId: string, fields: { name?: string; fixedCost?: number }]
  remove: [activityId: string]
  add: [name: string, fixedCost: number]
}>()

const newActivityName = ref('')
const newActivityCost = ref('')

function submitNewActivity(): void {
  if (newActivityName.value.trim().length === 0) return
  const cost = Number(newActivityCost.value)
  emit('add', newActivityName.value.trim(), Number.isFinite(cost) ? cost : 0)
  newActivityName.value = ''
  newActivityCost.value = ''
}

// Local drafts of in-progress edits, keyed by activity id, so typing
// doesn't fire a save on every keystroke -- only once the field loses
// focus and the value actually changed. Same pattern as
// WorkflowStageEditor's name/description drafts.
const nameDrafts = ref<Record<string, string>>({})
const costDrafts = ref<Record<string, string>>({})

function commitName(activity: ServiceCatalogActivity, value: string): void {
  delete nameDrafts.value[activity.id]
  if (value !== activity.name) emit('update', activity.id, { name: value })
}

function commitCost(activity: ServiceCatalogActivity, value: string): void {
  delete costDrafts.value[activity.id]
  const cost = Number(value)
  if (Number.isFinite(cost) && cost !== activity.fixedCost) emit('update', activity.id, { fixedCost: cost })
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <ol v-if="activities.length > 0" class="flex flex-col gap-3">
      <li
        v-for="activity in activities"
        :key="activity.id"
        class="flex flex-col gap-3 rounded-lg border border-border-light bg-bg-card p-4 sm:flex-row sm:items-start"
      >
        <div class="flex flex-1 flex-col gap-2 sm:flex-row">
          <TextInput
            :model-value="nameDrafts[activity.id] ?? activity.name"
            placeholder="Activity name"
            class="sm:flex-1"
            @update:model-value="nameDrafts[activity.id] = $event"
            @blur="commitName(activity, $event)"
          />
          <TextInput
            :model-value="costDrafts[activity.id] ?? String(activity.fixedCost)"
            type="number"
            inputmode="decimal"
            placeholder="Fixed cost"
            class="sm:w-40"
            @update:model-value="costDrafts[activity.id] = $event"
            @blur="commitCost(activity, $event)"
          />
        </div>

        <div class="flex shrink-0 items-center gap-2 self-end sm:self-start">
          <span class="text-sm font-medium text-text-muted">{{ formatCurrency(activity.fixedCost) }}</span>
          <IconButton :icon="Trash2" label="Remove activity" size="sm" variant="danger" @click="emit('remove', activity.id)" />
        </div>
      </li>
    </ol>
    <p v-else class="text-sm text-text-muted">No activities yet -- add one below.</p>

    <div class="flex flex-col gap-2 rounded-lg border border-dashed border-border-default p-4">
      <p class="text-sm font-medium text-text-secondary">Add Activity</p>
      <div class="flex flex-col gap-2 sm:flex-row">
        <TextInput v-model="newActivityName" placeholder="Activity name" class="sm:flex-1" />
        <TextInput v-model="newActivityCost" type="number" inputmode="decimal" placeholder="Fixed cost" class="sm:w-40" />
        <BaseButton :icon="Plus" variant="secondary" :disabled="newActivityName.trim().length === 0" @click="submitNewActivity">
          Add
        </BaseButton>
      </div>
    </div>
  </div>
</template>
