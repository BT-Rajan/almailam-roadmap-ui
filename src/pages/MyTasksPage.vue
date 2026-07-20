<script setup lang="ts">
import { computed, onMounted } from 'vue'

import BaseDrawer from '@/components/common/BaseDrawer.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TaskDetails from '@/components/task/TaskDetails.vue'
import TaskList from '@/components/task/TaskList.vue'
import { CURRENT_USER_NAME } from '@/constants/team'
import { useTaskStore } from '@/stores/taskStore'
import type { TaskPriority, TaskStatus } from '@/types/Task'

const taskStore = useTaskStore()

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
    <PageHeader title="My Tasks" :subtitle="`Work items assigned to ${CURRENT_USER_NAME}, sorted by due date.`" />

    <ErrorState v-if="taskStore.error" :description="taskStore.error" @retry="loadData" />

    <div v-else-if="taskStore.isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="6" />
    </div>

    <TaskList
      v-else
      :tasks="taskStore.myTasks"
      :get-project-by-id="taskStore.getProjectById"
      @open="taskStore.selectTask"
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
