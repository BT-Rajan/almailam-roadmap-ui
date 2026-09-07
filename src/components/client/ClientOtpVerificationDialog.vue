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
  // (see ClientWorkspacePage.vue), same "dumb dialog" pattern as every
  // other onboarding dialog in this folder.
  step: 'send' | 'enter-code'
  loading?: boolean
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
  <BaseDialog :model-value="modelValue" :title="t('client.otpVerificationDialog.title')" @update:model-value="emit('update:modelValue', $event)">
    <div v-if="step === 'send'" class="flex flex-col gap-4">
      <p class="text-sm text-text-secondary">
        {{ t('client.otpVerificationDialog.sendStepDescription', { email }) }}
      </p>
    </div>

    <div v-else class="flex flex-col gap-4">
      <p class="text-sm text-text-secondary">
        {{ t('client.otpVerificationDialog.codeSentTo', { email }) }}
      </p>
      <TextInput
        v-model="form.code"
        :label="t('client.otpVerificationDialog.codeLabel')"
        :placeholder="t('client.otpVerificationDialog.codePlaceholder')"
        inputmode="numeric"
        autocomplete="one-time-code"
        required
        :error="errors.code"
        :disabled="loading"
      />
      <BaseButton variant="ghost" size="sm" :disabled="loading" @click="handleSend">
        {{ t('client.otpVerificationDialog.resendCode') }}
      </BaseButton>
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="loading" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton v-if="step === 'send'" :loading="loading" @click="handleSend">
        {{ t('client.otpVerificationDialog.sendCode') }}
      </BaseButton>
      <BaseButton v-else :loading="loading" @click="handleConfirm">
        {{ t('client.otpVerificationDialog.confirm') }}
      </BaseButton>
    </template>
  </BaseDialog>
</template>
