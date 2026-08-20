<script setup lang="ts">
import { ShieldCheck } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TextInput from '@/components/common/TextInput.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import Alert from '@/components/common/Alert.vue'
import AuthCard from '@/components/auth/AuthCard.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { customerPortalService, CustomerPortalError } from '@/services/customerPortalService'

const router = useRouter()
const route = useRoute()

const mobileNumber = ref('')
const projectId = ref('')
const loading = ref(false)
const error = ref('')

onMounted(() => {
  // Set when redirected here after an expired/invalid session (see
  // CustomerProjectViewPage.vue) -- without this, someone bounced back
  // to login has no idea why and it looks like the app just broke.
  const reason = route.query.reason
  if (typeof reason === 'string') error.value = reason
})

const handleSubmit = async () => {
  error.value = ''

  if (!mobileNumber.value.trim() || !projectId.value.trim()) {
    error.value = 'Please enter both your mobile number and project ID.'
    return
  }

  loading.value = true
  try {
    const { accessToken } = await customerPortalService.verify(projectId.value.trim(), mobileNumber.value.trim())

    // The access token is real and backend-issued (verified against the
    // project's client mobile number), unlike the previous version of
    // this page, which just wrote a client-made-up "session" object to
    // localStorage regardless of whether the input was ever checked
    // against anything real.
    localStorage.setItem(
      'customerPortalSession',
      JSON.stringify({
        projectId: projectId.value.trim().toUpperCase(),
        accessToken,
        lastAccessed: new Date().toISOString(),
      }),
    )

    router.push({
      name: ROUTE_NAMES.CUSTOMER_PORTAL_PROJECT,
      params: { projectId: projectId.value.trim().toUpperCase() },
    })
  } catch (err) {
    error.value =
      err instanceof CustomerPortalError
        ? err.message
        : 'Invalid mobile number or project ID. Please verify and try again.'
  } finally {
    loading.value = false
  }
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter') handleSubmit()
}
</script>

<template>
  <AuthCard
    title="Track Your Project"
    subtitle="Enter your mobile number and project ID to view live progress, milestones, and deliverables."
  >
    <Alert v-if="error" variant="error" title="Couldn't verify your access" :description="error" class="mb-5" />

    <form class="flex flex-col gap-4" @submit.prevent="handleSubmit">
      <TextInput
        v-model="mobileNumber"
        type="tel"
        inputmode="tel"
        autocomplete="tel"
        label="Mobile Number"
        placeholder="Enter the mobile number on file"
        hint="The number registered with your project's client contact"
        required
        @keydown="handleKeydown"
      />

      <TextInput
        v-model="projectId"
        inputmode="numeric"
        label="Project ID"
        placeholder="Enter your project ID"
        hint="e.g., 2600001"
        required
        @keydown="handleKeydown"
      />

      <BaseButton
        type="submit"
        :loading="loading"
        :disabled="loading || !mobileNumber || !projectId"
        full-width
        class="mt-1"
      >
        Access Project
      </BaseButton>
    </form>

    <template #footer>
      <p class="flex items-center justify-center gap-1.5 text-center text-xs text-text-muted">
        <ShieldCheck class="h-3.5 w-3.5 shrink-0 text-text-muted" />
        Only you can view this project, verified against your registered mobile number.
      </p>
    </template>
  </AuthCard>
</template>
