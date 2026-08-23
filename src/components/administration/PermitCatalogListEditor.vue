<script setup lang="ts">
import { Plus, Trash2 } from '@lucide/vue'
import { ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import IconButton from '@/components/common/IconButton.vue'
import TextInput from '@/components/common/TextInput.vue'
import type { PermitCatalogItem } from '@/types/PermitCatalog'

defineProps<{
  permits: PermitCatalogItem[]
}>()

const emit = defineEmits<{
  update: [permitId: string, name: string]
  remove: [permitId: string]
  add: [name: string]
}>()

const newPermitName = ref('')

function submitNewPermit(): void {
  if (newPermitName.value.trim().length === 0) return
  emit('add', newPermitName.value.trim())
  newPermitName.value = ''
}

// Local draft of an in-progress name edit, keyed by permit id, so typing
// doesn't fire a save on every keystroke -- only once the field loses
// focus and the value actually changed. Same pattern as
// ServiceCatalogActivityEditor's name draft.
const nameDrafts = ref<Record<string, string>>({})

function commitName(permit: PermitCatalogItem, value: string): void {
  delete nameDrafts.value[permit.id]
  const trimmed = value.trim()
  if (trimmed.length > 0 && trimmed !== permit.name) emit('update', permit.id, trimmed)
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <ol v-if="permits.length > 0" class="flex flex-col gap-3">
      <li
        v-for="permit in permits"
        :key="permit.id"
        class="flex items-center gap-3 rounded-lg border border-border-light bg-bg-card p-4"
      >
        <TextInput
          :model-value="nameDrafts[permit.id] ?? permit.name"
          placeholder="Permit name"
          class="flex-1"
          @update:model-value="nameDrafts[permit.id] = $event"
          @blur="commitName(permit, $event)"
        />
        <IconButton :icon="Trash2" label="Remove permit" size="sm" variant="danger" @click="emit('remove', permit.id)" />
      </li>
    </ol>
    <p v-else class="text-sm text-text-muted">No permits yet -- add one below.</p>

    <div class="flex flex-col gap-2 rounded-lg border border-dashed border-border-default p-4">
      <p class="text-sm font-medium text-text-secondary">Add Permit</p>
      <div class="flex flex-col gap-2 sm:flex-row">
        <TextInput v-model="newPermitName" placeholder="Permit name" class="sm:flex-1" @keyup.enter="submitNewPermit" />
        <BaseButton :icon="Plus" variant="secondary" :disabled="newPermitName.trim().length === 0" @click="submitNewPermit">
          Add
        </BaseButton>
      </div>
    </div>
  </div>
</template>
