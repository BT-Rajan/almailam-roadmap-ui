<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import TextArea from '@/components/common/TextArea.vue'

interface Props {
  modelValue: boolean
  stepName: string | undefined
  isSubmitting?: boolean
}

const props = withDefaults(defineProps<Props>(), { isSubmitting: false })

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [reason: string]
}>()

const reason = ref('')

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) reason.value = ''
  },
)

const canConfirm = computed(() => reason.value.trim().length > 0)

function handleCancel(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  if (!canConfirm.value) return
  emit('confirm', reason.value.trim())
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    title="Waive Step"
    size="sm"
    @update:model-value="emit('update:modelValue', $event)"
    @close="handleCancel"
  >
    <p class="text-sm text-text-secondary">
      Waiving "{{ stepName }}" marks it as not applicable for this project rather than blocking the checklist. This is
      logged and can be undone later from this same view.
    </p>
    <TextArea v-model="reason" label="Reason" class="mt-4" :rows="3" required />

    <template #footer>
      <BaseButton variant="secondary" :disabled="isSubmitting" @click="handleCancel">Back</BaseButton>
      <BaseButton variant="danger" :loading="isSubmitting" :disabled="!canConfirm" @click="handleConfirm">
        Confirm Waiver
      </BaseButton>
    </template>
  </BaseDialog>
</template>
