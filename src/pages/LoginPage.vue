<script setup lang="ts">
import { LogIn } from '@lucide/vue'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useFormValidation } from '@/composables/useFormValidation'
import { useAuthStore } from '@/stores/authStore'
import { useLoginFormClear } from '@/composables/useLoginFormClear'
import { ApiError } from '@/services/httpClient'
import { validators } from '@/utils/validators'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

// Use the login form clear composable
const { form, clearAll } = useLoginFormClear()

const { errors, setRules, validateAll } = useFormValidation()
setRules({
  userId: [validators.required('User ID is required')],
  password: [validators.required('Password is required')],
})

const authError = ref<string>()
const isForgotPasswordOpen = ref(false)
const isSubmitting = ref(false)

async function signIn(): Promise<void> {
  authError.value = undefined

  if (!validateAll(form)) return

  isSubmitting.value = true

  try {
    await authStore.login(form.userId, form.password)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : undefined
    await router.push(redirect ?? { name: ROUTE_NAMES.DASHBOARD })
  } catch (error) {
    authError.value =
      error instanceof ApiError ? error.message : 'Unable to sign in. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}

/**
 * Clear login form and session data
 */
function clearLogin(): void {
  authError.value = undefined
  clearAll()
}
</script>

<template>
  <div>
    <h1 class="text-xl font-semibold text-[var(--color-text-primary)]">Sign in</h1>
    <p class="mt-1 text-sm text-[var(--color-text-secondary)]">
      Access the ServiceOS engineering consultancy workspace.
    </p>

    <form class="mt-6 flex flex-col gap-4" @submit.prevent="signIn">
      <TextInput
        v-model="form.userId"
        label="User ID"
        placeholder="Enter your user ID"
        required
        :error="errors.userId"
      />

      <TextInput
        v-model="form.password"
        type="password"
        label="Password"
        placeholder="Enter your password"
        required
        :error="errors.password"
      />

      <div class="flex items-center justify-between">
        <Checkbox v-model="form.rememberMe" label="Remember me" />
        <button
          type="button"
          class="text-sm font-medium text-primary-600 transition-colors duration-fast hover:text-primary-700"
          @click="isForgotPasswordOpen = true"
        >
          Forgot password?
        </button>
      </div>

      <p v-if="authError" class="rounded-lg bg-danger-50 px-3 py-2 text-sm text-danger-700">
        {{ authError }}
      </p>

      <div class="flex gap-3">
        <BaseButton type="submit" :icon="LogIn" :loading="isSubmitting" full-width>
          Sign In
        </BaseButton>
        <BaseButton
          type="button"
          variant="secondary"
          @click="clearLogin"
          :disabled="isSubmitting"
          full-width
        >
          Clear
        </BaseButton>
      </div>
    </form>

    <BaseDialog v-model="isForgotPasswordOpen" title="Forgot Password" size="sm">
      <p class="text-sm text-neutral-600">
        Please contact your system administrator to reset your password. This prototype does not send reset emails.
      </p>
      <template #footer>
        <BaseButton @click="isForgotPasswordOpen = false">Got It</BaseButton>
      </template>
    </BaseDialog>
  </div>
</template>
