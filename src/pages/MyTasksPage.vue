<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TaskFormDialog from '@/components/task/TaskFormDialog.vue'
import TaskList from '@/components/task/TaskList.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import type { TaskInput } from '@/services/taskService'
import { useAuthStore } from '@/stores/authStore'
import { useTaskStore } from '@/stores/taskStore'
import { useToastStore } from '@/stores/toastStore'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()
const taskStore = useTaskStore()
const toastStore = useToastStore()
const isCreateDialogOpen = ref(false)

function loadData(): void {
  taskStore.loadTasks()
}

onMounted(() => {
  if (taskStore.tasks.length === 0) loadData()
})

function openTask(taskId: string): void {
  router.push({ name: ROUTE_NAMES.TASK_WORKSPACE, params: { taskId } })
}

async function handleCreateTask(input: TaskInput): Promise<void> {
  try {
    const task = await taskStore.createTask(input)
    toastStore.show('success', t('task.taskActions.taskCreatedTitle'), t('task.taskActions.taskCreatedDescription', { title: task.title, assignee: task.assignedTo }))
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('task.taskActions.failedToCreateTask'), detail)
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
      @open="openTask"
    />

    <TaskFormDialog
      v-model="isCreateDialogOpen"
      :projects="taskStore.projects"
      @create="handleCreateTask"
    />
  </div>
</template>
