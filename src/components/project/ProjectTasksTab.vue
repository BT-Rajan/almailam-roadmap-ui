<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import TaskFormDialog from '@/components/task/TaskFormDialog.vue'
import TaskList from '@/components/task/TaskList.vue'
import { usePagination } from '@/composables/usePagination'
import { ROUTE_NAMES } from '@/constants/routeNames'
import type { TaskInput } from '@/services/taskService'
import { useClientStore } from '@/stores/clientStore'
import { useTaskStore } from '@/stores/taskStore'
import { useToastStore } from '@/stores/toastStore'
import type { Project, WorkflowStage } from '@/types/Project'

const props = defineProps<{
  project: Project
  // Which stage's Tasks tab this is -- Design/Supervision/Government
  // Submission each auto-create one system task per selected service
  // (see project_service.create_service_tasks and Task.selectedActivityId/
  // selectedPermitId/selectedSupervisionActivityId), as parallel tracks
  // that can all be active on the same project at once. When set to one
  // of those three, this tab scopes to that track's own service tasks
  // plus any plain, unlinked task -- not another track's service tasks
  // mixed in. Omitted (or any other stage) shows every project task
  // unfiltered, same as before.
  stageContext?: WorkflowStage
}>()

const taskStore = useTaskStore()
const toastStore = useToastStore()
const clientStore = useClientStore()
const router = useRouter()
const { t } = useI18n()
onMounted(() => {
  if (clientStore.clients.length === 0) clientStore.loadClients()
})

const projectTasks = computed(() => taskStore.tasksByProject(props.project.id))
const scopedProjectTasks = computed(() => {
  switch (props.stageContext) {
    case 'Design':
      return projectTasks.value.filter((task) => !task.selectedPermitId && !task.selectedSupervisionActivityId)
    case 'Supervision':
      return projectTasks.value.filter((task) => !task.selectedActivityId && !task.selectedPermitId)
    case 'Government Submission':
      return projectTasks.value.filter((task) => !task.selectedActivityId && !task.selectedSupervisionActivityId)
    default:
      return projectTasks.value
  }
})
// Every other list in the app uses this same usePagination/
// TablePagination.vue pair -- sliced client-side against the tasks
// already loaded into taskStore.
const { currentPage, pageSize, totalItems, totalPages, startIndex, endIndex, goToPage, setPageSize, resetPage } =
  usePagination(() => scopedProjectTasks.value.length)
const pagedProjectTasks = computed(() => scopedProjectTasks.value.slice(startIndex.value, endIndex.value))
watch(scopedProjectTasks, () => resetPage())
// Every task on this tab belongs to this one project, so its client is
// fixed too -- no need to resolve per-task like the cross-project Task
// Board/My Tasks views do.
const clientName = computed(() => clientStore.getClientById(props.project.clientId)?.companyName ?? t('project.unknownClient'))

const isCreateDialogOpen = ref(false)

async function handleCreateTask(input: TaskInput): Promise<void> {
  try {
    const task = await taskStore.createTask(input)
    toastStore.show('success', t('project.tasksTab.taskCreatedTitle'), t('project.tasksTab.taskCreatedDescription', { title: task.title, assignee: task.assignedTo }))
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('project.tasksTab.failedToCreateTask'), detail)
  }
}

// Opens the shared task workspace (see TaskWorkspacePage.vue) rather
// than this tab's own dialog -- the ?projectId query is what tells
// that page to confirm status/reassign changes first and refresh this
// project afterwards (a status change here can close out a Design/
// Permit/Supervision activity), and to send "back" here instead of the
// global Task Board.
function openTask(taskId: string): void {
  router.push({ name: ROUTE_NAMES.TASK_WORKSPACE, params: { taskId }, query: { projectId: props.project.id } })
}
</script>

<template>
  <div class="flex items-center justify-end no-print">
    <BaseButton size="sm" :icon="Plus" @click="isCreateDialogOpen = true">{{ t('project.tasksTab.newTask') }}</BaseButton>
  </div>

  <div v-if="taskStore.isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
    <SkeletonLoader :rows="6" />
  </div>

  <ErrorState v-else-if="taskStore.error" :description="taskStore.error" @retry="taskStore.loadTasks" />

  <TaskList
    v-else
    :tasks="pagedProjectTasks"
    :get-project-by-id="taskStore.getProjectById"
    :get-client-name-by-project-id="() => clientName"
    @open="openTask"
  />
  <TablePagination
    v-if="!taskStore.isLoading && !taskStore.error && totalItems > 0"
    class="rounded-xl border border-border-light"
    :current-page="currentPage"
    :total-pages="totalPages"
    :total-items="totalItems"
    :start-index="startIndex"
    :end-index="endIndex"
    :page-size="pageSize"
    @page-change="goToPage"
    @page-size-change="setPageSize"
  />

  <TaskFormDialog
    v-model="isCreateDialogOpen"
    :projects="[project]"
    :default-project-id="project.id"
    @create="handleCreateTask"
  />
</template>
