<script setup lang="ts">
import { LogIn } from '@lucide/vue'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import Alert from '@/components/common/Alert.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import TextInput from '@/components/common/TextInput.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { ApiError } from '@/services/httpClient'
import { useAuthStore } from '@/stores/authStore'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const employeeId = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleSubmit(): Promise<void> {
  error.value = ''
  if (!employeeId.value.trim() || !password.value.trim()) {
    error.value = 'Please enter both your Employee ID and password.'
    return
  }

  loading.value = true
  try {
    await authStore.loginWithEmployeeId(employeeId.value.trim(), password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : undefined
    await router.push(redirect ?? { name: ROUTE_NAMES.SITE_PORTAL_REPORT })
  } catch (err) {
    error.value = err instanceof ApiError ? err.message : 'Invalid Employee ID or password. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-[calc(100vh-64px)] items-center justify-center px-4 py-12">
    <div class="w-full max-w-md">
      <div class="glass-panel rounded-xl p-6 shadow-glass tablet:p-8">
        <div class="mb-6">
          <h1 class="text-2xl font-bold text-neutral-900">Site Engineer Sign In</h1>
          <p class="mt-2 text-sm text-neutral-600">File your daily status report and view your report history.</p>
        </div>

        <Alert v-if="error" variant="error" title="Couldn't sign you in" :description="error" class="mb-5" />

        <form class="flex flex-col gap-4" @submit.prevent="handleSubmit">
          <TextInput
            v-model="employeeId"
            label="Employee ID"
            placeholder="Enter your Employee ID"
            autocomplete="username"
            required
          />
          <TextInput
            v-model="password"
            type="password"
            label="Password"
            placeholder="Enter your password"
            autocomplete="current-password"
            required
          />
          <BaseButton type="submit" :icon="LogIn" :loading="loading" full-width>Sign In</BaseButton>
        </form>
      </div>
    </div>
  </div>
</template>
