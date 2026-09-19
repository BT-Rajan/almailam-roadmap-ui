<script setup lang="ts">
import { useRouter } from 'vue-router'

import WorkflowProgress from '@/components/project/WorkflowProgress.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import type { Project, ProjectWorkspaceTabKey } from '@/types/Project'

// The project's Workflow Progress stepper for pages that live outside
// ProjectWorkspacePage but belong to a project (New Permit Application,
// a permit application's own workspace) -- clicking a stage jumps to
// that stage in the project workspace, the same as the stepper on
// QuotationCreatePage/ContractCreatePage/PaymentPlanFormPage.
const props = defineProps<{
  project: Project
}>()

const router = useRouter()

function navigateToTab(tab: ProjectWorkspaceTabKey): void {
  router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId: props.project.id }, query: { tab } })
}
</script>

<template>
  <WorkflowProgress
    class="no-print"
    :current-stage="project.currentStage"
    :project-status="project.status"
    :includes-design="project.includesDesign"
    :includes-government-submission="project.includesGovernmentSubmission"
    :includes-supervision="project.includesSupervision"
    :selected-activities="project.selectedActivities"
    :selected-permits="project.selectedPermits"
    :selected-supervision-activities="project.selectedSupervisionActivities"
    @navigate-tab="navigateToTab"
  />
</template>
