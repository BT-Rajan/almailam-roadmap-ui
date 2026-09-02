<script setup lang="ts">
import { RefreshCw } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import BaseButton from '@/components/common/BaseButton.vue'
import CustomerProjectHeader from '@/components/customer/CustomerProjectHeader.vue'
import ProjectStageProgress from '@/components/customer/ProjectStageProgress.vue'
import MilestoneTimeline from '@/components/customer/MilestoneTimeline.vue'
import DeliverablesPanel from '@/components/customer/DeliverablesPanel.vue'
import ProjectUpdatesPanel from '@/components/customer/ProjectUpdatesPanel.vue'
import ProjectActivitiesPanel from '@/components/customer/ProjectActivitiesPanel.vue'
import ProjectBudgetPanel from '@/components/customer/ProjectBudgetPanel.vue'
import Card from '@/components/common/Card.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { customerPortalService } from '@/services/customerPortalService'
import { ApiError } from '@/services/httpClient'
import type { CustomerProjectStatus, ProjectActivityGroup, ProjectBudget, ProjectMilestone, ProjectDeliverable, ProjectUpdate } from '@/types/CustomerPortal'

const router = useRouter()
const route = useRoute()

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

async function loadProject(isManualRefresh = false): Promise<void> {
  loadError.value = ''
  if (isManualRefresh) {
    isRefreshing.value = true
  } else {
    isLoading.value = true
  }
  try {
    const projectId = route.params.projectId as string
    const view = await customerPortalService.getProjectView(projectId)
    projectData.value = view.project
    milestones.value = view.milestones
    deliverables.value = view.deliverables
    updates.value = view.updates
    activities.value = view.activities
    budget.value = view.budget
  } catch (error) {
    // Only a genuine 401/403 (the session really is invalid, or this
    // project isn't the customer's) means access itself is over. Any
    // other failure -- a dropped connection, a transient 500, a timeout
    // -- used to be treated exactly the same way: session wiped, forced
    // back to login with a "your session has expired" message that was
    // simply untrue. On a customer-facing, mobile-first page, that
    // turned an ordinary network hiccup into a full re-login with a
    // misleading explanation. Now: only a real auth failure logs anyone
    // out; everything else surfaces as a retryable error and leaves
    // whatever was already successfully loaded completely alone.
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      await router.push({
        name: ROUTE_NAMES.CUSTOMER_PORTAL_LOGIN,
        query: { reason: 'Your session has expired. Please sign in again.' },
      })
      return
    }
    loadError.value = "We couldn't reach the server. Please check your connection and try again."
  } finally {
    isLoading.value = false
    isRefreshing.value = false
  }
}

async function handleDownload(documentId: string): Promise<void> {
  const projectId = route.params.projectId as string
  if (!projectData.value) return
  downloadError.value = ''
  try {
    const blob = await customerPortalService.downloadDocument(projectId, documentId)
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
  <div v-if="isLoading" class="space-y-4">
    <SkeletonLoader variant="block" height="8rem" />
    <SkeletonLoader variant="block" height="12rem" />
    <SkeletonLoader variant="block" height="10rem" />
  </div>

  <div v-else-if="projectData" class="flex flex-col gap-4">
    <!-- A refresh failure (as opposed to the initial load) never hides
         what's already on screen -- the data shown is still whatever
         was last successfully loaded, just possibly stale, so this is
         a small inline notice rather than replacing the page. -->
    <div v-if="loadError" class="rounded-lg border border-danger-200 bg-danger-50 px-4 py-2.5 text-sm text-danger-700">
      {{ loadError }}
    </div>

    <!-- Top bar -->
    <div class="flex items-center justify-between gap-3">
      <div>
        <h1 class="text-lg font-semibold text-text-primary">Project Status</h1>
        <p class="text-xs text-text-muted">Project ID: {{ projectData.projectId }}</p>
      </div>
      <BaseButton variant="ghost" size="sm" :icon="RefreshCw" :loading="isRefreshing" @click="loadProject(true)">
        Refresh
      </BaseButton>
    </div>

    <!-- Project Header -->
    <CustomerProjectHeader :project="projectData" />

    <!-- Workflow Stage -->
    <ProjectStageProgress
      :current-stage="projectData.currentStage"
      :includes-design="projectData.includesDesign"
      :includes-supervision="projectData.includesSupervision"
    />

    <!-- Milestones -->
    <MilestoneTimeline :milestones="milestones" />

    <!-- Deliverables -->
    <p v-if="downloadError" class="text-xs text-danger-600">{{ downloadError }}</p>
    <DeliverablesPanel :deliverables="deliverables" @download="handleDownload" />

    <!-- Budget & Payments -->
    <ProjectBudgetPanel :budget="budget" />

    <!-- Scope of Work -->
    <ProjectActivitiesPanel :activities="activities" />

    <!-- Recent Updates -->
    <ProjectUpdatesPanel :updates="updates" />

    <!-- Contact / Quick Status -->
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
        <div class="border-t border-border-light pt-3 grid grid-cols-2 gap-2 text-xs">
          <div>
            <p class="text-text-secondary">Milestones</p>
            <p class="font-medium text-text-primary">{{ milestones.filter(m => m.status === 'completed').length }}/{{ milestones.length }} completed</p>
          </div>
          <div>
            <p class="text-text-secondary">Deliverables</p>
            <p class="font-medium text-text-primary">{{ deliverables.filter(d => d.status === 'approved').length }}/{{ deliverables.length }} approved</p>
          </div>
        </div>
      </div>
    </Card>

    <!-- Disclaimer -->
    <p class="text-xs text-text-muted">
      For confidential matters or detailed discussions, please contact the project management office directly.
    </p>
  </div>

  <ErrorState v-else :description="loadError || 'Unable to load this project.'" @retry="loadProject()" />
</template>
