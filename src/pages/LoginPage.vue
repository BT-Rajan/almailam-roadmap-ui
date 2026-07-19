<script setup lang="ts">
import { LogIn } from '@lucide/vue'
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useFormValidation } from '@/composables/useFormValidation'
import { useAuthStore } from '@/stores/authStore'
import { validators } from '@/utils/validators'

// Demo credentials - hardcoded for prototype purposes only.
const DEMO_CREDENTIALS = {
  userId: 'admin',
  password: 'Almailam@123',
}

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const form = reactive({
  userId: '',
  password: '',
  rememberMe: false,
})

const { errors, setRules, validateAll } = useFormValidation()
setRules({
  userId: [validators.required('User ID is required')],
  password: [validators.required('Password is required')],
})

const authError = ref<string>()
const isForgotPasswordOpen = ref(false)
const isSubmitting = ref(false)

function signIn(): void {
  authError.value = undefined

  if (!validateAll(form)) return

  isSubmitting.value = true

  if (form.userId === DEMO_CREDENTIALS.userId && form.password === DEMO_CREDENTIALS.password) {
    authStore.login()
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : undefined
    router.push(redirect ?? { name: ROUTE_NAMES.DASHBOARD })
  } else {
    authError.value = 'Invalid User ID or password. Please try again.'
  }

  isSubmitting.value = false
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

      <BaseButton type="submit" :icon="LogIn" :loading="isSubmitting" full-width>
        Sign In
      </BaseButton>
    </form>

    <p class="mt-4 text-center text-xs text-[var(--color-text-muted)]">
      Demo credentials — User ID: <span class="font-medium">admin</span> · Password:
      <span class="font-medium">Almailam@123</span>
    </p>

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
