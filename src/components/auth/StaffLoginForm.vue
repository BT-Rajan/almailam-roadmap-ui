<script setup lang="ts">
import { LogIn } from '@lucide/vue'
import { ref } from 'vue'

import Alert from '@/components/common/Alert.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useFormValidation } from '@/composables/useFormValidation'
import { ApiError } from '@/services/httpClient'
import { validators } from '@/utils/validators'

interface Props {
  idLabel: string
  idPlaceholder: string
  idAutocomplete?: string
  submitLabel?: string
  // Staff (application) login shows these; the Site Engineer Portal login
  // keeps things to just ID + password, so both stay opt-in rather than
  // baked into the shared form.
  showRememberMe?: boolean
  showForgotPassword?: boolean
  showClear?: boolean
  // Same tokens/session either way (see authStore.loginWithEmployeeId) --
  // only the endpoint differs, so the form itself just needs whichever
  // login function applies and stays agnostic to which one it is.
  loginFn: (id: string, password: string) => Promise<void>
}

const props = withDefaults(defineProps<Props>(), {
  idAutocomplete: 'username',
  submitLabel: 'Sign In',
  showRememberMe: false,
  showForgotPassword: false,
  showClear: false,
})

const emit = defineEmits<{
  success: []
}>()

const id = ref('')
const password = ref('')
const rememberMe = ref(false)
const authError = ref<string>()
const isForgotPasswordOpen = ref(false)
const isSubmitting = ref(false)

const { errors, setRules, validateAll } = useFormValidation()
setRules({
  id: [validators.required(`${props.idLabel} is required`)],
  password: [validators.required('Password is required')],
})

async function signIn(): Promise<void> {
  authError.value = undefined
  if (!validateAll({ id: id.value, password: password.value })) return

  isSubmitting.value = true
  try {
    await props.loginFn(id.value.trim(), password.value)
    emit('success')
  } catch (error) {
    authError.value = error instanceof ApiError ? error.message : 'Unable to sign in. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}

function clearLogin(): void {
  id.value = ''
  password.value = ''
  rememberMe.value = false
  authError.value = undefined
}
</script>

<template>
  <form class="flex flex-col gap-4" @submit.prevent="signIn">
    <TextInput
      v-model="id"
      :label="idLabel"
      :placeholder="idPlaceholder"
      :autocomplete="idAutocomplete"
      required
      :error="errors.id"
    />

    <TextInput
      v-model="password"
      type="password"
      label="Password"
      placeholder="Enter your password"
      autocomplete="current-password"
      required
      :error="errors.password"
    />

    <div v-if="showRememberMe || showForgotPassword" class="flex items-center justify-between">
      <Checkbox v-if="showRememberMe" v-model="rememberMe" label="Remember me" />
      <button
        v-if="showForgotPassword"
        type="button"
        class="text-sm font-medium text-primary-600 transition-colors duration-fast hover:text-primary-700"
        @click="isForgotPasswordOpen = true"
      >
        Forgot password?
      </button>
    </div>

    <Alert v-if="authError" variant="error" title="Couldn't sign you in" :description="authError" />

    <div class="flex gap-3">
      <BaseButton type="submit" :icon="LogIn" :loading="isSubmitting" full-width>
        {{ submitLabel }}
      </BaseButton>
      <BaseButton v-if="showClear" type="button" variant="secondary" :disabled="isSubmitting" full-width @click="clearLogin">
        Clear
      </BaseButton>
    </div>
  </form>

  <BaseDialog v-if="showForgotPassword" v-model="isForgotPasswordOpen" title="Forgot Password" size="sm">
    <p class="text-sm text-neutral-600">
      Please contact your system administrator to reset your password. This prototype does not send reset emails.
    </p>
    <template #footer>
      <BaseButton @click="isForgotPasswordOpen = false">Got It</BaseButton>
    </template>
  </BaseDialog>
</template>
