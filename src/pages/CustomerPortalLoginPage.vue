<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import TextInput from '@/components/common/TextInput.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import Alert from '@/components/common/Alert.vue'
import { customerPortalService, CustomerPortalError } from '@/services/customerPortalService'

const router = useRouter()

const mobileNumber = ref('')
const projectId = ref('')
const loading = ref(false)
const error = ref('')

const handleSubmit = async () => {
  error.value = ''

  if (!mobileNumber.value.trim() || !projectId.value.trim()) {
    error.value = 'Please enter both mobile number and project ID'
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
      name: 'customer-project',
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
  <div class="min-h-screen bg-gradient-to-br from-primary-50 to-info-50 flex flex-col items-center justify-center px-4 py-12">
    <div class="w-full max-w-md space-y-8">
      <!-- Logo -->
      <div class="text-center">
        <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-primary-600 text-sm font-semibold text-white mx-auto">
          SO
        </div>
        <h1 class="text-3xl font-bold text-neutral-900 mt-4">Project Tracking</h1>
        <p class="text-neutral-600 mt-2">Track your project progress in real time</p>
      </div>

      <!-- Login Card -->
      <Card class="bg-white shadow-lg">
        <div class="space-y-6">
          <div>
            <h2 class="text-xl font-semibold text-neutral-900">Verify Your Access</h2>
            <p class="text-sm text-neutral-600 mt-1">Enter your mobile number and project ID to view your project</p>
          </div>

          <!-- Error Alert -->
          <Alert v-if="error" variant="error" :title="error" />

          <!-- Form -->
          <div class="space-y-4">
            <TextInput
              v-model="mobileNumber"
              label="Mobile Number"
              placeholder="Enter the mobile number on file for this project"
              hint="The number registered with your project's client contact"
              @keydown="handleKeydown"
            />

            <TextInput
              v-model="projectId"
              label="Project ID"
              placeholder="Enter your project ID"
              hint="e.g., PRJ-2026-001"
              @keydown="handleKeydown"
            />

            <BaseButton
              :loading="loading"
              :disabled="loading || !mobileNumber || !projectId"
              class="w-full"
              @click="handleSubmit"
            >
              Access Project
            </BaseButton>
          </div>
        </div>
      </Card>

      <!-- Footer -->
      <div class="text-center">
        <p class="text-xs text-neutral-600">
          Protected access • Only you can view your project with your credentials
        </p>
        <p class="text-xs text-neutral-500 mt-2">
          &copy; {{ new Date().getFullYear() }} Almailam Engineering Consultants
        </p>
      </div>
    </div>
  </div>
</template>
