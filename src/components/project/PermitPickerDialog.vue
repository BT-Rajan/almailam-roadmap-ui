<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import type { PermitCatalogItem } from '@/types/PermitCatalog'

const props = defineProps<{
  modelValue: boolean
  permits: PermitCatalogItem[]
  selectedIds: string[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [value: PermitCatalogItem[]]
}>()

// Draft state -- edits here don't touch the caller's selection until
// "Add Permits" is clicked, so closing the dialog (Escape, backdrop
// click, Cancel) without confirming leaves the wizard's actual
// selection alone. Same pattern as ServicePickerDialog.
const { t } = useI18n()

const draftIds = ref<string[]>([])

// Re-seed the draft from whatever the caller already has selected every
// time the dialog opens, so re-opening to tweak a pick shows the
// current state rather than starting empty.
watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    draftIds.value = [...props.selectedIds]
  },
  { immediate: true },
)

function isSelected(permitId: string): boolean {
  return draftIds.value.includes(permitId)
}

function toggle(permitId: string): void {
  draftIds.value = isSelected(permitId) ? draftIds.value.filter((id) => id !== permitId) : [...draftIds.value, permitId]
}

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  const selected = props.permits.filter((permit) => draftIds.value.includes(permit.id))
  emit('confirm', selected)
  emit('update:modelValue', false)
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="t('project.permitPickerDialog.title')" size="md" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col rounded-lg border border-border-light">
      <div class="border-b border-border-light bg-bg-hover px-3 py-2 text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.permitPickerDialog.permits') }}</div>
      <div class="max-h-96 overflow-y-auto p-2">
        <p v-if="permits.length === 0" class="p-2 text-sm text-text-muted">{{ t('project.permitPickerDialog.noPermitsYet') }}</p>
        <div
          v-for="permit in permits"
          :key="permit.id"
          class="flex items-center gap-1.5 rounded-md px-2 py-1.5 hover:bg-bg-hover"
        >
          <Checkbox :model-value="isSelected(permit.id)" :label="permit.name" @update:model-value="toggle(permit.id)" />
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex w-full items-center justify-between gap-3">
        <p class="text-sm font-medium text-text-secondary">
          <span v-if="draftIds.length === 0" class="text-text-muted">{{ t('project.permitPickerDialog.noPermitsSelected') }}</span>
          <span v-else>{{ t('project.permitPickerDialog.permitsSelected', draftIds.length) }}</span>
        </p>
        <div class="flex gap-3">
          <BaseButton variant="secondary" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
          <BaseButton :disabled="draftIds.length === 0" @click="handleConfirm">{{ t('project.permitPickerDialog.addPermits') }}</BaseButton>
        </div>
      </div>
    </template>
  </BaseDialog>
</template>
