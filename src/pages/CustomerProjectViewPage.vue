<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import BaseButton from '@/components/common/BaseButton.vue'
import CustomerProjectHeader from '@/components/customer/CustomerProjectHeader.vue'
import MilestoneTimeline from '@/components/customer/MilestoneTimeline.vue'
import DeliverablesPanel from '@/components/customer/DeliverablesPanel.vue'
import ProjectUpdatesPanel from '@/components/customer/ProjectUpdatesPanel.vue'
import Card from '@/components/common/Card.vue'
import type { CustomerProjectStatus, ProjectMilestone, ProjectDeliverable, ProjectUpdate } from '@/types/CustomerPortal'

const router = useRouter()
const route = useRoute()

const authorized = ref(false)
const projectData = ref<CustomerProjectStatus | null>(null)
const milestones = ref<ProjectMilestone[]>([])
const deliverables = ref<ProjectDeliverable[]>([])
const updates = ref<ProjectUpdate[]>([])

// Mock data factory
const getMockProjectData = (projectId: string): CustomerProjectStatus => {
  const projects: Record<string, CustomerProjectStatus> = {
    'PROJ-2024-001': {
      projectId: 'PROJ-2024-001',
      projectName: 'Metro Rail Phase 2 Expansion',
      description: 'Design, planning, and execution of phase 2 expansion for metropolitan rail network',
      clientName: 'Municipal Transport Authority',
      startDate: '2024-01-15',
      expectedEndDate: '2024-12-31',
      status: 'active',
      progress: 65,
      summary:
        'Phase 2 is progressing well with most design approvals received. Infrastructure construction has commenced on 3 out of 5 sections. We are on track for the planned milestones.',
    },
    'PROJ-2024-002': {
      projectId: 'PROJ-2024-002',
      projectName: 'Highway Expansion & Modernization',
      description: 'Expansion and modernization of NH-44 highway corridor',
      clientName: 'State Transport Department',
      startDate: '2024-02-01',
      expectedEndDate: '2024-11-30',
      status: 'active',
      progress: 45,
      summary:
        'Survey and planning phase completed successfully. Environmental clearances obtained. Ready to commence construction activities in Q3.',
    },
    'PROJ-2024-003': {
      projectId: 'PROJ-2024-003',
      projectName: 'Water Treatment Plant Development',
      description: 'Construction and commissioning of water treatment facility',
      clientName: 'Municipal Authority',
      startDate: '2023-11-01',
      expectedEndDate: '2024-10-31',
      actualEndDate: '2024-10-20',
      status: 'completed',
      progress: 100,
      summary: 'Project successfully completed ahead of schedule. All systems tested and operational. Facility is now processing water at full capacity.',
    },
  }
  return projects[projectId] || projects['PROJ-2024-001']
}

const getMockMilestones = (projectId: string): ProjectMilestone[] => {
  const milestoneSets: Record<string, ProjectMilestone[]> = {
    'PROJ-2024-001': [
      {
        id: 'm1',
        title: 'Design Approval',
        description: 'Obtain all necessary design approvals from stakeholders',
        dueDate: '2024-03-31',
        status: 'completed',
        completedDate: '2024-03-25',
      },
      {
        id: 'm2',
        title: 'Environmental Clearance',
        description: 'Secure environmental impact assessment and clearance',
        dueDate: '2024-05-31',
        status: 'completed',
        completedDate: '2024-05-20',
      },
      {
        id: 'm3',
        title: 'Construction Phase 1',
        description: 'Complete foundation and initial infrastructure work',
        dueDate: '2024-09-30',
        status: 'in-progress',
      },
      {
        id: 'm4',
        title: 'Construction Phase 2',
        description: 'Complete structural and systems installation',
        dueDate: '2024-12-31',
        status: 'pending',
      },
    ],
    'PROJ-2024-002': [
      {
        id: 'm1',
        title: 'Survey & Assessment',
        dueDate: '2024-04-30',
        status: 'completed',
        completedDate: '2024-04-15',
      },
      {
        id: 'm2',
        title: 'Environmental Clearance',
        dueDate: '2024-06-30',
        status: 'in-progress',
      },
      {
        id: 'm3',
        title: 'Land Acquisition',
        dueDate: '2024-09-30',
        status: 'pending',
      },
    ],
    'PROJ-2024-003': [
      {
        id: 'm1',
        title: 'Site Preparation',
        dueDate: '2024-01-31',
        status: 'completed',
        completedDate: '2024-01-20',
      },
      {
        id: 'm2',
        title: 'Construction',
        dueDate: '2024-08-31',
        status: 'completed',
        completedDate: '2024-08-25',
      },
      {
        id: 'm3',
        title: 'Testing & Commissioning',
        dueDate: '2024-10-31',
        status: 'completed',
        completedDate: '2024-10-20',
      },
    ],
  }
  return milestoneSets[projectId] || milestoneSets['PROJ-2024-001']
}

const getMockDeliverables = (projectId: string): ProjectDeliverable[] => {
  const deliverableSets: Record<string, ProjectDeliverable[]> = {
    'PROJ-2024-001': [
      {
        id: 'd1',
        name: 'Design Documentation',
        description: 'Complete design and technical specifications',
        type: 'PDF',
        status: 'approved',
        deliveryDate: '2024-03-20',
        approvalDate: '2024-03-25',
      },
      {
        id: 'd2',
        name: 'Safety Plan',
        description: 'Comprehensive safety and risk management plan',
        type: 'PDF',
        status: 'approved',
        deliveryDate: '2024-04-10',
        approvalDate: '2024-04-15',
      },
      {
        id: 'd3',
        name: 'Progress Report Q2',
        description: 'Second quarter progress and status report',
        type: 'PDF',
        status: 'delivered',
        deliveryDate: '2024-06-30',
      },
      {
        id: 'd4',
        name: 'Progress Report Q3',
        description: 'Third quarter progress and status report',
        type: 'PDF',
        status: 'pending',
      },
    ],
    'PROJ-2024-002': [
      {
        id: 'd1',
        name: 'Survey Report',
        type: 'PDF',
        status: 'approved',
        deliveryDate: '2024-04-20',
        approvalDate: '2024-04-25',
      },
      {
        id: 'd2',
        name: 'Environmental Impact Assessment',
        type: 'PDF',
        status: 'delivered',
        deliveryDate: '2024-06-15',
      },
    ],
    'PROJ-2024-003': [
      {
        id: 'd1',
        name: 'Design & Specifications',
        type: 'PDF',
        status: 'approved',
        deliveryDate: '2023-12-15',
        approvalDate: '2023-12-20',
      },
      {
        id: 'd2',
        name: 'Construction Progress Reports',
        type: 'PDF',
        status: 'approved',
        deliveryDate: '2024-09-30',
        approvalDate: '2024-10-01',
      },
      {
        id: 'd3',
        name: 'As-Built Documentation',
        type: 'PDF',
        status: 'approved',
        deliveryDate: '2024-10-20',
        approvalDate: '2024-10-20',
      },
    ],
  }
  return deliverableSets[projectId] || deliverableSets['PROJ-2024-001']
}

const getMockUpdates = (projectId: string): ProjectUpdate[] => {
  const updateSets: Record<string, ProjectUpdate[]> = {
    'PROJ-2024-001': [
      {
        id: 'u1',
        date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        title: 'Section 3 Construction Commenced',
        description: 'Construction activities for section 3 have officially started with site mobilization complete.',
        type: 'status',
      },
      {
        id: 'u2',
        date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
        title: 'Progress Report Q3 Published',
        description: 'Quarterly progress report for Q3 is now available in deliverables.',
        type: 'deliverable',
      },
      {
        id: 'u3',
        date: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
        title: 'Construction Phase 1 Milestone Achieved',
        description: 'All foundation work for phase 1 successfully completed on schedule.',
        type: 'milestone',
      },
    ],
    'PROJ-2024-002': [
      {
        id: 'u1',
        date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
        title: 'Environmental Clearance In Progress',
        description: 'Environmental impact assessment review is underway with authorities.',
        type: 'status',
      },
    ],
    'PROJ-2024-003': [
      {
        id: 'u1',
        date: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString(),
        title: 'Project Successfully Completed',
        description: 'All project objectives achieved and facility is operational.',
        type: 'milestone',
      },
    ],
  }
  return updateSets[projectId] || updateSets['PROJ-2024-001']
}

const handleLogout = () => {
  localStorage.removeItem('customerPortalSession')
  router.push({ name: 'customer-portal' })
}

onMounted(() => {
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

    // Load mock data
    const projectId = route.params.projectId as string
    projectData.value = getMockProjectData(projectId)
    milestones.value = getMockMilestones(projectId)
    deliverables.value = getMockDeliverables(projectId)
    updates.value = getMockUpdates(projectId)
  } catch {
    router.push({ name: 'customer-portal' })
  }
})
</script>

<template>
  <div v-if="!authorized" class="py-12 text-center">
    <p class="text-neutral-600">Verifying access...</p>
  </div>

  <div v-else-if="projectData" class="max-w-7xl mx-auto px-4 tablet:px-6 py-8 space-y-8">
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
