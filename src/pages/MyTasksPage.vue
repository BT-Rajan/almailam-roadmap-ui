<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TaskDetails from '@/components/task/TaskDetails.vue'
import TaskFormDialog from '@/components/task/TaskFormDialog.vue'
import TaskList from '@/components/task/TaskList.vue'
import type { TaskInput } from '@/services/taskService'
import { useAuthStore } from '@/stores/authStore'
import { useTaskStore } from '@/stores/taskStore'
import { useToastStore } from '@/stores/toastStore'
import type { TaskPriority, TaskSeverity, TaskStatus } from '@/types/Task'

const { t } = useI18n()
const authStore = useAuthStore()
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
  () => taskStore.getProjectById(taskStore.selectedTask?.projectId ?? '')?.projectName ?? t('task.unknownProject'),
)

const selectedTaskClientName = computed(() => taskStore.getClientNameByProjectId(taskStore.selectedTask?.projectId ?? ''))

function loadData(): void {
  taskStore.loadTasks()
}

onMounted(() => {
  if (taskStore.tasks.length === 0) loadData()
})

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
    <PageHeader :title="t('task.myTasksPage.title')" :subtitle="t('task.myTasksPage.subtitle', { name: authStore.user?.name ?? t('task.myTasksPage.you') })">
      <template #actions>
        <BaseButton :icon="Plus" @click="isCreateDialogOpen = true">{{ t('task.myTasksPage.addTask') }}</BaseButton>
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
      :get-client-name-by-project-id="taskStore.getClientNameByProjectId"
      @open="taskStore.selectTask"
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
