<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import { CLIENT_ONBOARDING_ALLOWED_TRANSITIONS, CLIENT_ONBOARDING_STATES_REQUIRING_REASON } from '@/constants/clientOptions'
import type { ClientOnboardingState } from '@/types/Client'

const props = defineProps<{
  modelValue: boolean
  currentState: ClientOnboardingState
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: { onboardingState: ClientOnboardingState; reason?: string }]
}>()

const { t } = useI18n()

const options = computed(() =>
  (CLIENT_ONBOARDING_ALLOWED_TRANSITIONS[props.currentState] ?? []).map((state) => ({ label: state, value: state })),
)

const form = reactive({
  onboardingState: '' as ClientOnboardingState | '',
  reason: '',
})

const errors = reactive({ onboardingState: '', reason: '' })

const reasonRequired = computed(() =>
  form.onboardingState ? CLIENT_ONBOARDING_STATES_REQUIRING_REASON.includes(form.onboardingState) : false,
)

// Reset the form to a clean slate each time the dialog opens, defaulting
// to the only option when there's just one valid next state.
watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    form.onboardingState = options.value.length === 1 ? (options.value[0].value as ClientOnboardingState) : ''
    form.reason = ''
    errors.onboardingState = ''
    errors.reason = ''
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  errors.onboardingState = form.onboardingState ? '' : 'Please select a status'
  errors.reason = reasonRequired.value && !form.reason.trim() ? 'A reason is required for this status change' : ''
  if (errors.onboardingState || errors.reason) return

  emit('confirm', {
    onboardingState: form.onboardingState as ClientOnboardingState,
    reason: form.reason.trim() || undefined,
  })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="t('client.onboardingStatusDialog.title')" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <SelectBox v-model="form.onboardingState" :label="t('client.onboardingStatusDialog.newStatus')" required :options="options" :error="errors.onboardingState" />
      <TextArea
        v-model="form.reason"
        :label="t('client.onboardingStatusDialog.reason')"
        :required="reasonRequired"
        :error="errors.reason"
        :hint="reasonRequired ? t('client.onboardingStatusDialog.reasonRequiredHint') : t('common.optional')"
        :rows="3"
      />
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">{{ t('common.confirm') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
