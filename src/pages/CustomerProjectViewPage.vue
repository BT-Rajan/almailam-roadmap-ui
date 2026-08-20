<script setup lang="ts">
import { RefreshCw } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import BaseButton from '@/components/common/BaseButton.vue'
import CustomerProjectHeader from '@/components/customer/CustomerProjectHeader.vue'
import MilestoneTimeline from '@/components/customer/MilestoneTimeline.vue'
import DeliverablesPanel from '@/components/customer/DeliverablesPanel.vue'
import ProjectUpdatesPanel from '@/components/customer/ProjectUpdatesPanel.vue'
import ProjectActivitiesPanel from '@/components/customer/ProjectActivitiesPanel.vue'
import ProjectBudgetPanel from '@/components/customer/ProjectBudgetPanel.vue'
import Card from '@/components/common/Card.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { customerPortalService, CustomerPortalError } from '@/services/customerPortalService'
import type { CustomerProjectStatus, ProjectActivityGroup, ProjectBudget, ProjectMilestone, ProjectDeliverable, ProjectUpdate } from '@/types/CustomerPortal'

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
const activities = ref<ProjectActivityGroup[]>([])
const budget = ref<ProjectBudget | null>(null)

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
  loadError.value = ''
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
    activities.value = view.activities
    budget.value = view.budget
  } catch (error) {
    // Only a genuine 401 (the token really is invalid, expired, or for
    // the wrong project -- see get_project_for_token on the backend)
    // means the session itself is actually over. Any other failure --
    // a dropped connection, a transient 500, a timeout -- used to be
    // treated exactly the same way: session wiped, forced back to
    // login with a "your session has expired" message that was simply
    // untrue. On a customer-facing, mobile-first page, that turned an
    // ordinary network hiccup into a full re-verification with a
    // misleading explanation. Now: only a real auth failure logs
    // anyone out; everything else surfaces as a retryable error and
    // leaves the existing token (and, on a refresh, whatever was
    // already successfully loaded) completely alone.
    if (error instanceof CustomerPortalError && error.status === 401) {
      redirectToLogin('Your session has expired. Please verify your access again.')
      return
    }
    loadError.value = "We couldn't reach the server. Please check your connection and try again."
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
    <!-- A refresh failure (as opposed to the initial load) never hides
         what's already on screen -- the data shown is still whatever
         was last successfully loaded, just possibly stale, so this is
         a small inline notice rather than replacing the page. -->
    <div v-if="loadError" class="rounded-lg border border-danger-200 bg-danger-50 px-4 py-2.5 text-sm text-danger-700">
      {{ loadError }}
    </div>

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
        <ProjectActivitiesPanel :activities="activities" />
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

    <!-- Budget & Payments -->
    <ProjectBudgetPanel :budget="budget" />

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

  <div v-else class="mx-auto max-w-lg px-4 py-8">
    <ErrorState :description="loadError || 'Unable to load this project.'" @retry="loadProject()" />
  </div>
</template>
