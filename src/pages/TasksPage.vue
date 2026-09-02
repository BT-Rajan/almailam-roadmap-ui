<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TaskBoard from '@/components/task/TaskBoard.vue'
import TaskDetails from '@/components/task/TaskDetails.vue'
import TaskFormDialog from '@/components/task/TaskFormDialog.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import type { TaskInput } from '@/services/taskService'
import { useTaskStore } from '@/stores/taskStore'
import { useToastStore } from '@/stores/toastStore'
import { useUserStore } from '@/stores/userStore'
import { getNextTaskStatus } from '@/utils/taskHelpers'
import type { TaskPriority, TaskSeverity, TaskStatus } from '@/types/Task'
import type { SelectOption } from '@/types/Ui'

const router = useRouter()
const taskStore = useTaskStore()
const toastStore = useToastStore()
const userStore = useUserStore()
onMounted(() => {
  if (userStore.users.length === 0) userStore.loadUsers()
})
const isCreateDialogOpen = ref(false)

const PRIORITY_OPTIONS: SelectOption[] = [
  { label: 'All Priorities', value: 'All' },
  { label: 'High', value: 'High' },
  { label: 'Medium', value: 'Medium' },
  { label: 'Low', value: 'Low' },
]

const projectOptions = computed<SelectOption[]>(() => [
  { label: 'All Projects', value: 'All' },
  ...taskStore.projects.map((project) => ({ label: project.projectName, value: project.id })),
])

// Values here are display names, not user ids -- this only filters the
// already-loaded task list client-side (taskStore.filteredTasks
// compares task.assignedTo, which is always a resolved name), unlike
// TaskFormDialog/TaskAssignmentCard which write an assignment back to
// the backend and need real ids for that.
const assigneeOptions = computed<SelectOption[]>(() => [
  { label: 'All Assignees', value: 'All' },
  ...userStore.users.filter((user) => user.status === 'Active').map((user) => ({ label: user.name, value: user.name })),
])

const isDrawerOpen = computed({
  get: () => Boolean(taskStore.selectedTaskId),
  set: (value: boolean) => {
    if (!value) taskStore.clearSelectedTask()
  },
})

const selectedTaskProjectName = computed(
  () => taskStore.getProjectById(taskStore.selectedTask?.projectId ?? '')?.projectName ?? 'Unknown Project',
)

const selectedTaskClientName = computed(() => taskStore.getClientNameByProjectId(taskStore.selectedTask?.projectId ?? ''))

function loadData(): void {
  taskStore.loadTasks()
}

onMounted(() => {
  if (taskStore.tasks.length === 0) loadData()
})

function openTask(taskId: string): void {
  taskStore.selectTask(taskId)
}

function advanceTask(taskId: string): void {
  const task = taskStore.tasks.find((item) => item.id === taskId)
  if (!task) return
  const next = getNextTaskStatus(task.status)
  if (next) taskStore.updateTaskStatus(taskId, next)
}

async function handleStatusChange(status: TaskStatus): Promise<void> {
  if (!taskStore.selectedTaskId) return
  try {
    await taskStore.updateTaskStatus(taskStore.selectedTaskId, status)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to update status', detail)
  }
}

async function handlePriorityChange(priority: TaskPriority): Promise<void> {
  if (!taskStore.selectedTaskId) return
  try {
    await taskStore.updateTaskPriority(taskStore.selectedTaskId, priority)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to update priority', detail)
  }
}

async function handleSeverityChange(severity: TaskSeverity): Promise<void> {
  if (!taskStore.selectedTaskId) return
  try {
    await taskStore.updateTaskSeverity(taskStore.selectedTaskId, severity)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to update severity', detail)
  }
}

async function handleReassign(assignee: string): Promise<void> {
  if (!taskStore.selectedTaskId) return
  try {
    await taskStore.updateTaskAssignee(taskStore.selectedTaskId, assignee)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to reassign task', detail)
  }
}

async function handleCreateTask(input: TaskInput): Promise<void> {
  try {
    const task = await taskStore.createTask(input)
    toastStore.show('success', 'Task created', `"${task.title}" was assigned to ${task.assignedTo}.`)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to create task', detail)
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader title="Task Board" subtitle="Track project work items by status across the team.">
      <template #actions>
        <BaseButton variant="secondary" @click="router.push({ name: ROUTE_NAMES.MY_TASKS })">
          My Tasks
        </BaseButton>
        <BaseButton :icon="Plus" @click="isCreateDialogOpen = true">Add Task</BaseButton>
      </template>
    </PageHeader>

    <FilterBar
      :show-search="false"
      :has-active-filters="taskStore.hasActiveFilters"
      @clear="taskStore.clearFilters"
    >
      <template #filters>
        <div class="w-40">
          <SelectBox
            :model-value="taskStore.priorityFilter"
            :options="PRIORITY_OPTIONS"
            @update:model-value="taskStore.setPriorityFilter($event as TaskPriority | 'All')"
          />
        </div>
        <div class="w-56">
          <SelectBox
            :model-value="taskStore.projectFilter"
            :options="projectOptions"
            @update:model-value="taskStore.setProjectFilter($event)"
          />
        </div>
        <div class="w-48">
          <SelectBox
            :model-value="taskStore.assigneeFilter"
            :options="assigneeOptions"
            @update:model-value="taskStore.setAssigneeFilter($event)"
          />
        </div>
      </template>
    </FilterBar>

    <ErrorState v-if="taskStore.error" :description="taskStore.error" @retry="loadData" />

    <div v-else-if="taskStore.isLoading" class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
      <div v-for="placeholder in 3" :key="placeholder" class="rounded-xl border border-border-light bg-bg-card p-4">
        <SkeletonLoader :rows="5" />
      </div>
    </div>

    <TaskBoard
      v-else
      :tasks-by-status="taskStore.tasksByStatus"
      :get-project-by-id="taskStore.getProjectById"
      :get-client-name-by-project-id="taskStore.getClientNameByProjectId"
      @open="openTask"
      @advance="advanceTask"
    />

    <BaseDrawer v-model="isDrawerOpen" :title="taskStore.selectedTask?.id" width="md">
      <TaskDetails
        v-if="taskStore.selectedTask"
        :task="taskStore.selectedTask"
        :project-name="selectedTaskProjectName"
        :client-name="selectedTaskClientName"
        @status-change="handleStatusChange"
        @priority-change="handlePriorityChange"
        @severity-change="handleSeverityChange"
        @reassign="handleReassign"
      />
    </BaseDrawer>

    <TaskFormDialog
      v-model="isCreateDialogOpen"
      :projects="taskStore.projects"
      @create="handleCreateTask"
    />
  </div>
</template>
