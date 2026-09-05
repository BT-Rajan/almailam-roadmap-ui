<script setup lang="ts">
import { FolderOpen } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { customerPortalService, type CustomerProjectOption } from '@/services/customerPortalService'

const router = useRouter()
const { t } = useI18n()

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

onMounted(loadProjects)
</script>

<template>
  <div class="flex flex-col gap-4">
    <div v-if="isLoading" class="space-y-3">
      <SkeletonLoader variant="block" height="4rem" />
      <SkeletonLoader variant="block" height="4rem" />
    </div>

    <ErrorState v-else-if="loadError" :description="loadError" @retry="loadProjects" />

    <ErrorState
      v-else-if="projects.length === 0"
      :title="t('customer.projectsPage.noProjectsFound')"
      :description="t('customer.projectsPage.noProjectsFoundDescription')"
      :retry-label="t('customer.projectsPage.checkAgain')"
      @retry="loadProjects"
    />

    <template v-else>
      <h1 class="text-lg font-semibold text-text-primary">{{ t('customer.projectsPage.yourProjects') }}</h1>
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
          <p class="text-xs text-text-muted">{{ t('customer.projectsPage.projectIdLabel', { id: project.projectId }) }}</p>
        </div>
      </button>
    </template>
  </div>
</template>
