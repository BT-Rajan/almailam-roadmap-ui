<script setup lang="ts">
import { computed, onMounted } from 'vue'
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
import { TEAM_MEMBERS } from '@/constants/team'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useTaskStore } from '@/stores/taskStore'
import { getNextTaskStatus } from '@/utils/taskHelpers'
import type { TaskPriority, TaskStatus } from '@/types/Task'
import type { SelectOption } from '@/types/Ui'

const router = useRouter()
const taskStore = useTaskStore()

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

const assigneeOptions = computed<SelectOption[]>(() => [
  { label: 'All Assignees', value: 'All' },
  ...TEAM_MEMBERS.map((member) => ({ label: member.name, value: member.name })),
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

function handleStatusChange(status: TaskStatus): void {
  if (taskStore.selectedTaskId) taskStore.updateTaskStatus(taskStore.selectedTaskId, status)
}

function handlePriorityChange(priority: TaskPriority): void {
  if (taskStore.selectedTaskId) taskStore.updateTaskPriority(taskStore.selectedTaskId, priority)
}

function handleReassign(assignee: string): void {
  if (taskStore.selectedTaskId) taskStore.updateTaskAssignee(taskStore.selectedTaskId, assignee)
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader title="Task Board" subtitle="Track project work items by status across the team.">
      <template #actions>
        <BaseButton variant="secondary" @click="router.push({ name: ROUTE_NAMES.MY_TASKS })">
          My Tasks
        </BaseButton>
      </template>
    </PageHeader>

    <FilterBar
      :search-value="taskStore.searchTerm"
      search-placeholder="Search by task title"
      :has-active-filters="taskStore.hasActiveFilters"
      @update:search-value="taskStore.setSearchTerm"
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
      @open="openTask"
      @advance="advanceTask"
    />

    <BaseDrawer v-model="isDrawerOpen" :title="taskStore.selectedTask?.id" width="md">
      <TaskDetails
        v-if="taskStore.selectedTask"
        :task="taskStore.selectedTask"
        :project-name="selectedTaskProjectName"
        @status-change="handleStatusChange"
        @priority-change="handlePriorityChange"
        @reassign="handleReassign"
      />
    </BaseDrawer>
  </div>
</template>
