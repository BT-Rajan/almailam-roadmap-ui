<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TaskDetails from '@/components/task/TaskDetails.vue'
import TaskList from '@/components/task/TaskList.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useTaskStore } from '@/stores/taskStore'
import type { Project } from '@/types/Project'
import type { TaskPriority, TaskStatus } from '@/types/Task'

const props = defineProps<{
  project: Project
}>()

const router = useRouter()
const taskStore = useTaskStore()

const projectTasks = computed(() => taskStore.tasksByProject(props.project.id))

const isDrawerOpen = computed({
  get: () => Boolean(taskStore.selectedTaskId),
  set: (value: boolean) => {
    if (!value) taskStore.clearSelectedTask()
  },
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
  <div class="flex items-center justify-end">
    <BaseButton variant="ghost" size="sm" class="no-print" @click="router.push({ name: ROUTE_NAMES.TASKS })">
      View Task Board
    </BaseButton>
  </div>

  <div v-if="taskStore.isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
    <SkeletonLoader :rows="6" />
  </div>

  <ErrorState v-else-if="taskStore.error" :description="taskStore.error" @retry="taskStore.loadTasks" />

  <TaskList v-else :tasks="projectTasks" :get-project-by-id="taskStore.getProjectById" @open="taskStore.selectTask" />

  <BaseDrawer v-model="isDrawerOpen" :title="taskStore.selectedTask?.id" width="md">
    <TaskDetails
      v-if="taskStore.selectedTask"
      :task="taskStore.selectedTask"
      :project-name="project.projectName"
      @status-change="handleStatusChange"
      @priority-change="handlePriorityChange"
      @reassign="handleReassign"
    />
  </BaseDrawer>
</template>
