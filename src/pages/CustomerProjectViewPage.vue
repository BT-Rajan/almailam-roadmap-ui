<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import BaseButton from '@/components/common/BaseButton.vue'
import CustomerProjectHeader from '@/components/customer/CustomerProjectHeader.vue'
import MilestoneTimeline from '@/components/customer/MilestoneTimeline.vue'
import DeliverablesPanel from '@/components/customer/DeliverablesPanel.vue'
import ProjectUpdatesPanel from '@/components/customer/ProjectUpdatesPanel.vue'
import Card from '@/components/common/Card.vue'
import { customerPortalService } from '@/services/customerPortalService'
import type { CustomerProjectStatus, ProjectMilestone, ProjectDeliverable, ProjectUpdate } from '@/types/CustomerPortal'

const router = useRouter()
const route = useRoute()

const authorized = ref(false)
const projectData = ref<CustomerProjectStatus | null>(null)
const milestones = ref<ProjectMilestone[]>([])
const deliverables = ref<ProjectDeliverable[]>([])
const updates = ref<ProjectUpdate[]>([])

const handleLogout = () => {
  localStorage.removeItem('customerPortalSession')
  router.push({ name: 'customer-portal' })
}

onMounted(async () => {
  // Verify session
  const session = localStorage.getItem('customerPortalSession')
  if (!session) {
    router.push({ name: 'customer-portal' })
    return
  }

  try {
    const parsedSession = JSON.parse(session)
    if (parsedSession.projectId !== route.params.projectId) {
      router.push({ name: 'customer-portal' })
      return
    }

    authorized.value = true

    const projectId = route.params.projectId as string
    const view = await customerPortalService.getProjectView(projectId)
    projectData.value = view.project
    milestones.value = view.milestones
    deliverables.value = view.deliverables
    updates.value = view.updates
  } catch {
    router.push({ name: 'customer-portal' })
  }
})
</script>

<template>
  <div v-if="!authorized || !projectData" class="py-12 text-center">
    <p class="text-neutral-600">Verifying access...</p>
  </div>

  <div v-else class="max-w-7xl mx-auto px-4 tablet:px-6 py-8 space-y-8">
    <!-- Header with Logout -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-neutral-900">{{ projectData.projectName }}</h1>
        <p class="text-neutral-600 mt-1">Project ID: {{ projectData.projectId }}</p>
      </div>
      <BaseButton variant="ghost" @click="handleLogout"> Logout </BaseButton>
    </div>

    <!-- Project Header -->
    <CustomerProjectHeader :project="projectData" />

    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 laptop:grid-cols-3 gap-6">
      <!-- Left Column: Milestones and Updates -->
      <div class="laptop:col-span-2 space-y-6">
        <MilestoneTimeline :milestones="milestones" />
      </div>

      <!-- Right Column: Info Cards -->
      <div class="space-y-6">
        <!-- Contact Info -->
        <Card>
          <template #header>
            <h3 class="font-semibold text-neutral-900">Need Help?</h3>
          </template>
          <div class="space-y-3 text-sm">
            <div>
              <p class="text-neutral-600 font-medium">Project Manager</p>
              <p class="text-neutral-900">Rajesh Kumar</p>
              <p class="text-neutral-500 text-xs">+91 98765 43210</p>
            </div>
            <div class="border-t border-border-light pt-3">
              <p class="text-neutral-600 font-medium">Support Email</p>
              <p class="text-neutral-900 break-all">projects@almailam.in</p>
            </div>
          </div>
        </Card>

        <!-- Project Status Summary -->
        <Card>
          <template #header>
            <h3 class="font-semibold text-neutral-900">Quick Status</h3>
          </template>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-neutral-600">Milestones</span>
              <span class="font-medium">{{ milestones.filter(m => m.status === 'completed').length }}/{{ milestones.length }} completed</span>
            </div>
            <div class="flex justify-between">
              <span class="text-neutral-600">Deliverables</span>
              <span class="font-medium">{{ deliverables.filter(d => d.status === 'approved').length }}/{{ deliverables.length }} approved</span>
            </div>
            <div class="flex justify-between">
              <span class="text-neutral-600">Overall Progress</span>
              <span class="font-medium">{{ projectData.progress }}%</span>
            </div>
          </div>
        </Card>
      </div>
    </div>

    <!-- Deliverables and Updates -->
    <div class="grid grid-cols-1 laptop:grid-cols-2 gap-6">
      <DeliverablesPanel :deliverables="deliverables" />
      <ProjectUpdatesPanel :updates="updates" />
    </div>

    <!-- Disclaimer -->
    <Card class="bg-neutral-50 border border-neutral-200">
      <div class="text-xs text-neutral-600 space-y-1">
        <p>
          <strong>Note:</strong> This customer portal provides real-time access to your project information. Information is updated regularly.
        </p>
        <p>For confidential matters or detailed discussions, please contact the project management office directly.</p>
      </div>
    </Card>
  </div>
</template>
