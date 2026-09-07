<script setup lang="ts">
import { reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import TextInput from '@/components/common/TextInput.vue'

const props = defineProps<{
  modelValue: boolean
  email: string
  // 'send': nothing sent yet (or the dialog was just reopened) -- show
  // the "Send Verification Code" step. 'enter-code': a code is on its
  // way -- show the code input, with a resend link. Controlled by the
  // parent page, which is also what actually calls the send/verify API
  // (see ClientWorkspacePage.vue and ProjectRequirementTab.vue, its two
  // callers), same "dumb dialog" pattern as every other confirmation
  // dialog in this app.
  step: 'send' | 'enter-code'
  loading?: boolean
  // Both default to the generic "verify with the client by email" copy
  // -- override when the thing being confirmed needs saying (e.g.
  // "Confirm Scope of Work" instead of "Verify Client Email").
  title?: string
  sendStepDescription?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  send: []
  confirm: [payload: { code: string }]
}>()

const { t } = useI18n()

const form = reactive({ code: '' })
const errors = reactive({ code: '' })

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    form.code = ''
    errors.code = ''
  },
)

watch(
  () => props.step,
  () => {
    form.code = ''
    errors.code = ''
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleSend(): void {
  emit('send')
}

function handleConfirm(): void {
  errors.code = form.code.trim() ? '' : 'Please enter the code'
  if (errors.code) return
  emit('confirm', { code: form.code.trim() })
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="title ?? t('common.otpVerificationDialog.title')"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div v-if="step === 'send'" class="flex flex-col gap-4">
      <p class="text-sm text-text-secondary">
        {{ sendStepDescription ?? t('common.otpVerificationDialog.sendStepDescription', { email }) }}
      </p>
    </div>

    <div v-else class="flex flex-col gap-4">
      <p class="text-sm text-text-secondary">
        {{ t('common.otpVerificationDialog.codeSentTo', { email }) }}
      </p>
      <TextInput
        v-model="form.code"
        :label="t('common.otpVerificationDialog.codeLabel')"
        :placeholder="t('common.otpVerificationDialog.codePlaceholder')"
        inputmode="numeric"
        autocomplete="one-time-code"
        required
        :error="errors.code"
        :disabled="loading"
      />
      <BaseButton variant="ghost" size="sm" :disabled="loading" @click="handleSend">
        {{ t('common.otpVerificationDialog.resendCode') }}
      </BaseButton>
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="loading" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton v-if="step === 'send'" :loading="loading" @click="handleSend">
        {{ t('common.otpVerificationDialog.sendCode') }}
      </BaseButton>
      <BaseButton v-else :loading="loading" @click="handleConfirm">
        {{ t('common.otpVerificationDialog.confirm') }}
      </BaseButton>
    </template>
  </BaseDialog>
</template>
