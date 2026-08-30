<script setup lang="ts">
import { LogIn } from '@lucide/vue'
import { onMounted, ref } from 'vue'

import Alert from '@/components/common/Alert.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useFormValidation } from '@/composables/useFormValidation'
import { ApiError } from '@/services/httpClient'
import type { ToastVariant } from '@/types/Toast'
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
  // Shown once, on mount -- e.g. "You were signed out after 30 minutes of
  // inactivity." after useIdleLogout redirects here. Not a validation
  // error, so it defaults to the neutral 'info' styling rather than
  // reusing the red sign-in-failure alert below.
  initialMessage?: string
  initialMessageVariant?: ToastVariant
  // Same tokens/session for all three portals (see authStore.login) --
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
  initialMessage: undefined,
  initialMessageVariant: 'info',
})

const emit = defineEmits<{
  success: []
}>()

const id = ref('')
const password = ref('')
const rememberMe = ref(false)
const authError = ref<string>()
const infoMessage = ref<string>()
const isForgotPasswordOpen = ref(false)
const isSubmitting = ref(false)
const idInputRef = ref<InstanceType<typeof TextInput>>()

onMounted(() => {
  if (props.initialMessage) infoMessage.value = props.initialMessage
  idInputRef.value?.focus()
})

const { errors, setRules, validateAll } = useFormValidation()
setRules({
  id: [validators.required(`${props.idLabel} is required`)],
  password: [validators.required('Password is required')],
})

async function signIn(): Promise<void> {
  // Native form submission (Enter key) is a separate trigger path from
  // BaseButton's click handler -- its own click-level guard doesn't cover
  // this, so the re-entrancy check has to live here too.
  if (isSubmitting.value) return

  authError.value = undefined
  infoMessage.value = undefined
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
      ref="idInputRef"
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

    <Alert v-if="infoMessage" :variant="initialMessageVariant" title="Signed out" :description="infoMessage" />
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
    <p class="text-sm text-text-secondary">
      Please contact your system administrator to reset your password. This prototype does not send reset emails.
    </p>
    <template #footer>
      <BaseButton @click="isForgotPasswordOpen = false">Got It</BaseButton>
    </template>
  </BaseDialog>
</template>
