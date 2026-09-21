<script setup lang="ts">
import { Lock } from '@lucide/vue'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useAuth } from '@/composables/useAuthComposable'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useToastStore } from '@/stores/toastStore'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const { t } = useI18n()
const router = useRouter()
const toastStore = useToastStore()
const { changePassword } = useAuth()

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const formError = ref<string>()
const isSaving = ref(false)

watch(
  () => props.modelValue,
  (open) => {
    if (!open) resetForm()
  },
)

function resetForm(): void {
  currentPassword.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
  formError.value = undefined
}

// Mirrors the backend's own rejection (ChangePasswordRequest.not_trivial in
// backend/app/schemas/auth.py): a password that's entirely letters or
// entirely digits is rejected even past the length check. Checked here too
// so that gets caught immediately instead of only after a round trip to
// the server for the exact same rejection.
function isTrivialPassword(value: string): boolean {
  return /^\p{L}+$/u.test(value) || /^\p{Nd}+$/u.test(value)
}

const canSubmit = computed(
  () =>
    currentPassword.value.trim().length > 0 &&
    newPassword.value.length >= 8 &&
    !isTrivialPassword(newPassword.value) &&
    confirmPassword.value.length > 0,
)

function closeDialog(): void {
  if (isSaving.value) return
  emit('update:modelValue', false)
}

async function submit(): Promise<void> {
  formError.value = undefined

  if (newPassword.value.length < 8) {
    formError.value = 'New password must be at least 8 characters.'
    return
  }
  if (isTrivialPassword(newPassword.value)) {
    formError.value = 'Password must mix letters, numbers, or symbols.'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    formError.value = 'New password and confirmation do not match.'
    return
  }

  isSaving.value = true
  try {
    await changePassword(currentPassword.value, newPassword.value)
    emit('update:modelValue', false)
    toastStore.show('success', t('auth.changePasswordDialog.passwordChangedTitle'), t('auth.changePasswordDialog.passwordChangedDescription'))
    router.push({ name: ROUTE_NAMES.LOGIN })
  } catch (error) {
    formError.value = error instanceof Error && error.message ? error.message : 'Failed to change password.'
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <BaseDialog :title="t('auth.changePassword')" size="sm" :model-value="modelValue" :closable="!isSaving" @update:model-value="closeDialog">
    <div class="flex flex-col gap-4">
      <TextInput
        v-model="currentPassword"
        type="password"
        :label="t('auth.changePasswordDialog.currentPassword')"
        :placeholder="t('auth.changePasswordDialog.currentPasswordPlaceholder')"
        autocomplete="current-password"
        :icon="Lock"
        required
      />
      <TextInput
        v-model="newPassword"
        type="password"
        :label="t('auth.changePasswordDialog.newPassword')"
        :placeholder="t('auth.changePasswordDialog.newPasswordPlaceholder')"
        :hint="t('auth.changePasswordDialog.newPasswordHint')"
        autocomplete="new-password"
        :icon="Lock"
        required
      />
      <TextInput
        v-model="confirmPassword"
        type="password"
        :label="t('auth.changePasswordDialog.confirmNewPassword')"
        :placeholder="t('auth.changePasswordDialog.confirmNewPasswordPlaceholder')"
        autocomplete="new-password"
        :icon="Lock"
        required
        :error="formError"
      />
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="isSaving" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :disabled="!canSubmit" :loading="isSaving" @click="submit">{{ t('auth.changePassword') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
