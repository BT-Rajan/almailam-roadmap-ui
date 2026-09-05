<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'

const props = defineProps<{
  modelValue: boolean
  title: string
  currentValue: string
  allowedTransitions: Record<string, string[]>
  isReasonRequired: (newStatus: string) => boolean
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: { value: string; reason?: string }]
}>()

const { t } = useI18n()

const options = computed(() => (props.allowedTransitions[props.currentValue] ?? []).map((value) => ({ label: value, value })))

const form = reactive({ value: '', reason: '' })
const errors = reactive({ value: '', reason: '' })

const reasonRequired = computed(() => (form.value ? props.isReasonRequired(form.value) : false))

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    form.value = options.value.length === 1 ? options.value[0].value : ''
    form.reason = ''
    errors.value = ''
    errors.reason = ''
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  errors.value = form.value ? '' : 'Please select an option'
  errors.reason = reasonRequired.value && !form.reason.trim() ? 'A reason is required for this change' : ''
  if (errors.value || errors.reason) return

  emit('confirm', { value: form.value, reason: form.reason.trim() || undefined })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="title" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <SelectBox v-model="form.value" :label="t('project.transitionDialog.newStatus')" required :options="options" :error="errors.value" />
      <TextArea
        v-model="form.reason"
        :label="t('project.transitionDialog.reason')"
        :required="reasonRequired"
        :error="errors.reason"
        :hint="reasonRequired ? t('project.transitionDialog.reasonRequiredHint') : t('common.optional')"
        :rows="3"
      />
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">{{ t('common.confirm') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
