<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import TextInput from '@/components/common/TextInput.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import Alert from '@/components/common/Alert.vue'

const router = useRouter()

const mobileNumber = ref('')
const projectId = ref('')
const loading = ref(false)
const error = ref('')

const mobileRegex = /^[6-9]\d{9}$/

const handleSubmit = async () => {
  error.value = ''

  // Validate inputs
  if (!mobileNumber.value.trim() || !projectId.value.trim()) {
    error.value = 'Please enter both mobile number and project ID'
    return
  }

  if (!mobileRegex.test(mobileNumber.value)) {
    error.value = 'Please enter a valid 10-digit mobile number'
    return
  }

  if (projectId.value.trim().length < 5) {
    error.value = 'Project ID should be at least 5 characters'
    return
  }

  loading.value = true

  // Simulate verification delay
  setTimeout(() => {
    // Mock verification - in production this would call an API
    const validProjects: Record<string, string[]> = {
      'PROJ-2024-001': ['9876543210', '9876543211'],
      'PROJ-2024-002': ['9876543212', '9876543213'],
      'PROJ-2024-003': ['9876543214'],
    }

    if (validProjects[projectId.value.toUpperCase()]?.includes(mobileNumber.value)) {
      // Store session
      localStorage.setItem(
        'customerPortalSession',
        JSON.stringify({
          projectId: projectId.value.toUpperCase(),
          mobileNumber: mobileNumber.value,
          lastAccessed: new Date().toISOString(),
        })
      )

      router.push({
        name: 'customer-project',
        params: { projectId: projectId.value.toUpperCase() },
      })
    } else {
      error.value = 'Invalid mobile number or project ID. Please verify and try again.'
      loading.value = false
    }
  }, 800)
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter') handleSubmit()
}

// Demo projects info
const demoProjects = [
  { id: 'PROJ-2024-001', name: 'Metro Rail Phase 2', phone: '+91 9876543210' },
  { id: 'PROJ-2024-002', name: 'Highway Expansion', phone: '+91 9876543212' },
  { id: 'PROJ-2024-003', name: 'Water Treatment Plant', phone: '+91 9876543214' },
]
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
              placeholder="Enter 10-digit mobile number"
              hint="e.g., 9876543210"
              @keydown="handleKeydown"
            />

            <TextInput
              v-model="projectId"
              label="Project ID"
              placeholder="Enter your project ID"
              hint="e.g., PROJ-2024-001"
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

      <!-- Info Card -->
      <Card class="bg-info-50 border border-info-200">
        <div class="space-y-3">
          <h3 class="font-semibold text-info-900">Demo Project IDs</h3>
          <div class="space-y-2">
            <div v-for="project in demoProjects" :key="project.id" class="text-sm text-info-800">
              <p class="font-medium">{{ project.name }}</p>
              <p class="text-xs text-info-700">ID: <code class="bg-info-100 px-2 py-1 rounded">{{ project.id }}</code></p>
              <p class="text-xs text-info-700">Mobile: {{ project.phone }}</p>
            </div>
          </div>
          <p class="text-xs text-info-600 pt-2 border-t border-info-200">
            💡 Use the project ID and mobile number above to access demo projects
          </p>
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
