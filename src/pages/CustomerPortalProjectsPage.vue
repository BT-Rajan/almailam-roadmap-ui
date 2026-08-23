<script setup lang="ts">
import { FolderOpen } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { customerPortalService, type CustomerProjectOption } from '@/services/customerPortalService'
import { useAuthStore } from '@/stores/authStore'

const router = useRouter()
const authStore = useAuthStore()

const isLoading = ref(true)
const loadError = ref('')
const projects = ref<CustomerProjectOption[]>([])

async function loadProjects(): Promise<void> {
  isLoading.value = true
  loadError.value = ''
  try {
    const result = await customerPortalService.listMyProjects()
    projects.value = result
    // The common case: a customer with one project goes straight in,
    // same as before when login itself carried a single project ID --
    // a picker only makes sense once there's actually something to pick.
    if (result.length === 1) {
      await router.replace({ name: ROUTE_NAMES.CUSTOMER_PORTAL_PROJECT, params: { projectId: result[0].projectId } })
    }
  } catch {
    loadError.value = "We couldn't load your projects. Please check your connection and try again."
  } finally {
    isLoading.value = false
  }
}

function openProject(projectId: string): void {
  router.push({ name: ROUTE_NAMES.CUSTOMER_PORTAL_PROJECT, params: { projectId } })
}

async function handleLogout(): Promise<void> {
  await authStore.logout()
  await router.push({ name: ROUTE_NAMES.CUSTOMER_PORTAL_LOGIN })
}

onMounted(loadProjects)
</script>

<template>
  <div class="mx-auto max-w-2xl space-y-4 px-4 py-8 tablet:px-6">
    <div v-if="isLoading" class="space-y-3">
      <SkeletonLoader variant="block" height="4rem" />
      <SkeletonLoader variant="block" height="4rem" />
    </div>

    <ErrorState v-else-if="loadError" :description="loadError" @retry="loadProjects" />

    <ErrorState
      v-else-if="projects.length === 0"
      title="No projects found"
      description="No projects are linked to your account yet. Please contact your project engineer."
      retry-label="Check Again"
      @retry="loadProjects"
    />

    <template v-else>
      <div class="flex items-center justify-between">
        <h1 class="text-xl font-semibold text-text-primary">Your Projects</h1>
        <button type="button" class="text-sm text-text-muted hover:text-text-secondary" @click="handleLogout">
          Logout
        </button>
      </div>
      <button
        v-for="project in projects"
        :key="project.projectId"
        type="button"
        class="glass-panel flex w-full items-center gap-3 rounded-xl p-4 text-left shadow-glass transition hover:shadow-md"
        @click="openProject(project.projectId)"
      >
        <FolderOpen class="h-5 w-5 shrink-0 text-primary-600" />
        <div class="min-w-0">
          <p class="truncate font-medium text-text-primary">{{ project.projectName }}</p>
          <p class="text-xs text-text-muted">Project ID: {{ project.projectId }}</p>
        </div>
      </button>
    </template>
  </div>
</template>
