<script setup lang="ts">
import { RefreshCw } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import BaseButton from '@/components/common/BaseButton.vue'
import CustomerProjectHeader from '@/components/customer/CustomerProjectHeader.vue'
import MilestoneTimeline from '@/components/customer/MilestoneTimeline.vue'
import DeliverablesPanel from '@/components/customer/DeliverablesPanel.vue'
import ProjectUpdatesPanel from '@/components/customer/ProjectUpdatesPanel.vue'
import Card from '@/components/common/Card.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { customerPortalService } from '@/services/customerPortalService'
import type { CustomerProjectStatus, ProjectMilestone, ProjectDeliverable, ProjectUpdate } from '@/types/CustomerPortal'

const router = useRouter()
const route = useRoute()

const authorized = ref(false)
const isLoading = ref(true)
const isRefreshing = ref(false)
const loadError = ref('')
const downloadError = ref('')
const projectData = ref<CustomerProjectStatus | null>(null)
const milestones = ref<ProjectMilestone[]>([])
const deliverables = ref<ProjectDeliverable[]>([])
const updates = ref<ProjectUpdate[]>([])

function getAccessToken(): string | null {
  const session = localStorage.getItem('customerPortalSession')
  if (!session) return null
  try {
    const parsed = JSON.parse(session)
    if (parsed.projectId !== route.params.projectId || !parsed.accessToken) return null
    return parsed.accessToken as string
  } catch {
    return null
  }
}

function redirectToLogin(reason?: string): void {
  localStorage.removeItem('customerPortalSession')
  router.push({ name: ROUTE_NAMES.CUSTOMER_PORTAL_LOGIN, query: reason ? { reason } : undefined })
}

const handleLogout = () => redirectToLogin()

async function loadProject(isManualRefresh = false): Promise<void> {
  const accessToken = getAccessToken()
  if (!accessToken) {
    redirectToLogin()
    return
  }

  authorized.value = true
  if (isManualRefresh) {
    isRefreshing.value = true
  } else {
    isLoading.value = true
  }
  try {
    const projectId = route.params.projectId as string
    const view = await customerPortalService.getProjectView(projectId, accessToken)
    projectData.value = view.project
    milestones.value = view.milestones
    deliverables.value = view.deliverables
    updates.value = view.updates
  } catch {
    // The access token may have expired (it's valid for 60 minutes) or
    // been for a different project -- send them back to verify again,
    // with a query param so the login page can actually explain why,
    // rather than navigating away before any message here is ever seen.
    redirectToLogin('Your session has expired. Please verify your access again.')
    return
  } finally {
    isLoading.value = false
    isRefreshing.value = false
  }
}

async function handleDownload(documentId: string): Promise<void> {
  const accessToken = getAccessToken()
  const projectId = route.params.projectId as string
  if (!accessToken || !projectData.value) return
  downloadError.value = ''
  try {
    const blob = await customerPortalService.downloadDocument(projectId, documentId, accessToken)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = documentId
    link.click()
    URL.revokeObjectURL(url)
  } catch {
    downloadError.value = "This document isn't available for download yet."
  }
}

onMounted(() => loadProject())
</script>

<template>
  <div v-if="!authorized || isLoading" class="mx-auto max-w-3xl space-y-4 px-4 py-8 tablet:px-6">
    <SkeletonLoader variant="block" height="8rem" />
    <SkeletonLoader variant="block" height="12rem" />
    <SkeletonLoader variant="block" height="10rem" />
  </div>

  <div v-else-if="projectData" class="mx-auto max-w-7xl space-y-6 px-4 py-6 tablet:space-y-8 tablet:px-6 tablet:py-8">
    <!-- Top bar -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <p class="text-sm text-text-muted">Project ID: <span class="font-medium text-text-secondary">{{ projectData.projectId }}</span></p>
      <div class="flex items-center gap-2">
        <BaseButton variant="ghost" size="sm" :icon="RefreshCw" :loading="isRefreshing" @click="loadProject(true)">
          Refresh
        </BaseButton>
        <BaseButton variant="ghost" size="sm" @click="handleLogout">Logout</BaseButton>
      </div>
    </div>

    <!-- Project Header -->
    <CustomerProjectHeader :project="projectData" />

    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <!-- Left Column: Milestones -->
      <div class="space-y-6 laptop:col-span-2">
        <MilestoneTimeline :milestones="milestones" />
      </div>

      <!-- Right Column: Info Cards -->
      <div class="space-y-6">
        <!-- Contact Info -->
        <Card>
          <template #header>
            <h3 class="font-semibold text-text-primary">Need Help?</h3>
          </template>
          <div class="space-y-3 text-sm">
            <div>
              <p class="font-medium text-text-secondary">Project Engineer</p>
              <p class="text-text-primary">{{ projectData.engineerName }}</p>
            </div>
            <div class="border-t border-border-light pt-3">
              <p class="font-medium text-text-secondary">Support Email</p>
              <a :href="`mailto:${projectData.supportEmail}`" class="break-all text-primary-600 hover:underline">
                {{ projectData.supportEmail }}
              </a>
              <p v-if="projectData.supportPhone" class="mt-1">
                <a :href="`tel:${projectData.supportPhone}`" class="text-xs text-primary-600 hover:underline">
                  {{ projectData.supportPhone }}
                </a>
              </p>
            </div>
          </div>
        </Card>

        <!-- Project Status Summary -->
        <Card>
          <template #header>
            <h3 class="font-semibold text-text-primary">Quick Status</h3>
          </template>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-text-secondary">Milestones</span>
              <span class="font-medium">{{ milestones.filter(m => m.status === 'completed').length }}/{{ milestones.length }} completed</span>
            </div>
            <div class="flex justify-between">
              <span class="text-text-secondary">Deliverables</span>
              <span class="font-medium">{{ deliverables.filter(d => d.status === 'approved').length }}/{{ deliverables.length }} approved</span>
            </div>
            <div class="flex justify-between">
              <span class="text-text-secondary">Overall Progress</span>
              <span class="font-medium">{{ projectData.progress }}%</span>
            </div>
          </div>
        </Card>
      </div>
    </div>

    <!-- Deliverables and Updates -->
    <div class="grid grid-cols-1 gap-6 laptop:grid-cols-2">
      <div class="space-y-2">
        <p v-if="downloadError" class="text-xs text-danger-600">{{ downloadError }}</p>
        <DeliverablesPanel :deliverables="deliverables" @download="handleDownload" />
      </div>
      <ProjectUpdatesPanel :updates="updates" />
    </div>

    <!-- Disclaimer -->
    <Card class="border border-border-default bg-bg-secondary">
      <div class="space-y-1 text-xs text-text-secondary">
        <p>
          <strong>Note:</strong> This customer portal provides access to your project information. Use "Refresh" above for the latest status.
        </p>
        <p>For confidential matters or detailed discussions, please contact the project management office directly.</p>
      </div>
    </Card>
  </div>

  <div v-else class="py-12 text-center text-text-secondary">
    {{ loadError || 'Unable to load this project.' }}
  </div>
</template>
