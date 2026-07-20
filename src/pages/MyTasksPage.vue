<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TaskDetails from '@/components/task/TaskDetails.vue'
import TaskFormDialog from '@/components/task/TaskFormDialog.vue'
import TaskList from '@/components/task/TaskList.vue'
import { CURRENT_USER_NAME } from '@/constants/team'
import type { TaskInput } from '@/services/taskService'
import { useTaskStore } from '@/stores/taskStore'
import { useToastStore } from '@/stores/toastStore'
import type { TaskPriority, TaskSeverity, TaskStatus } from '@/types/Task'

const taskStore = useTaskStore()
const toastStore = useToastStore()
const isCreateDialogOpen = ref(false)

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

function handleSeverityChange(severity: TaskSeverity): void {
  if (taskStore.selectedTaskId) taskStore.updateTaskSeverity(taskStore.selectedTaskId, severity)
}

function handleReassign(assignee: string): void {
  if (taskStore.selectedTaskId) taskStore.updateTaskAssignee(taskStore.selectedTaskId, assignee)
}

async function handleCreateTask(input: TaskInput): Promise<void> {
  const task = await taskStore.createTask(input)
  toastStore.show('success', 'Task created', `"${task.title}" was assigned to ${task.assignedTo}.`)
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader title="My Tasks" :subtitle="`Work items assigned to ${CURRENT_USER_NAME}, sorted by due date.`">
      <template #actions>
        <BaseButton :icon="Plus" @click="isCreateDialogOpen = true">Add Task</BaseButton>
      </template>
    </PageHeader>

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
