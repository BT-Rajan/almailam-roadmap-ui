<script setup lang="ts">
import { Lock } from '@lucide/vue'
import { computed, ref, watch } from 'vue'
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

const canSubmit = computed(
  () =>
    currentPassword.value.trim().length > 0 &&
    newPassword.value.length >= 8 &&
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
  if (newPassword.value !== confirmPassword.value) {
    formError.value = 'New password and confirmation do not match.'
    return
  }

  isSaving.value = true
  try {
    await changePassword(currentPassword.value, newPassword.value)
    emit('update:modelValue', false)
    toastStore.show('success', 'Password changed', 'Please log in again with your new password.')
    router.push({ name: ROUTE_NAMES.LOGIN })
  } catch (error) {
    formError.value = error instanceof Error && error.message ? error.message : 'Failed to change password.'
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <BaseDialog title="Change Password" size="sm" :model-value="modelValue" :closable="!isSaving" @update:model-value="closeDialog">
    <div class="flex flex-col gap-4">
      <TextInput
        v-model="currentPassword"
        type="password"
        label="Current Password"
        placeholder="Enter current password"
        autocomplete="current-password"
        :icon="Lock"
        required
      />
      <TextInput
        v-model="newPassword"
        type="password"
        label="New Password"
        placeholder="At least 8 characters"
        autocomplete="new-password"
        :icon="Lock"
        required
      />
      <TextInput
        v-model="confirmPassword"
        type="password"
        label="Confirm New Password"
        placeholder="Re-enter new password"
        autocomplete="new-password"
        :icon="Lock"
        required
        :error="formError"
      />
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="isSaving" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :disabled="!canSubmit" :loading="isSaving" @click="submit">Change Password</BaseButton>
    </template>
  </BaseDialog>
</template>
