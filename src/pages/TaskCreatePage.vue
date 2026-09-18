<script setup lang="ts">
import { ArrowLeft, ArrowRight } from '@lucide/vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import TimePicker from '@/components/common/TimePicker.vue'
import { useFormValidation } from '@/composables/useFormValidation'
import { useLocale } from '@/composables/useLocale'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useAuthStore } from '@/stores/authStore'
import { useClientStore } from '@/stores/clientStore'
import { useTaskStore } from '@/stores/taskStore'
import { useToastStore } from '@/stores/toastStore'
import { useUserStore } from '@/stores/userStore'
import type { TaskPriority, TaskSeverity } from '@/types/Task'
import type { SelectOption } from '@/types/Ui'
import { validators } from '@/utils/validators'

// Replaces TaskFormDialog.vue's modal -- a dedicated route (/tasks/new)
// like NewProjectWizardPage/NewClientWizardPage, instead of a popup.
// TasksPage, MyTasksPage, ProjectTasksTab, and ActivityCalendarPage all
// navigate here now instead of opening a dialog.

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isRtl } = useLocale()
const authStore = useAuthStore()
const userStore = useUserStore()
const clientStore = useClientStore()
const taskStore = useTaskStore()
const toastStore = useToastStore()

const backIcon = computed(() => (isRtl.value ? ArrowRight : ArrowLeft))

// ?projectId= prefills the project field everywhere it's passed
// (e.g. ActivityCalendarPage's "create a follow-up task" flow).
// ?locked=1 additionally restricts the Project field to just that one
// project and hides it from being changed -- ProjectTasksTab.vue's own
// "Add Task" button always did this (it only ever passed a single-item
// project list), since a task added from inside one project's own
// Tasks tab shouldn't quietly end up filed under a different project.
const queryProjectId = computed(() => {
  const value = route.query.projectId
  return typeof value === 'string' ? value : undefined
})
const isProjectLocked = computed(() => route.query.locked === '1')
const queryTitle = computed(() => {
  const value = route.query.title
  return typeof value === 'string' ? value : undefined
})

onMounted(() => {
  if (userStore.users.length === 0) userStore.loadUsers()
  if (clientStore.clients.length === 0) clientStore.loadClients()
  if (taskStore.projects.length === 0) taskStore.loadTasks()
  form.title = queryTitle.value ?? ''
  form.projectId = queryProjectId.value ?? ''
  form.assignedTo = authStore.user?.id ?? ''
})

const form = reactive({
  title: '',
  projectId: '',
  // A real user id (e.g. "USR-004"), not a display name -- the backend
  // resolves assignedTo to a real user server-side (task_service.py's
  // _resolve_assignee), so sending anything else fails validation
  // outright.
  assignedTo: '',
  priority: 'Medium' as TaskPriority,
  severity: 'Minor' as TaskSeverity,
  startDate: '',
  dueDate: '',
  dueTime: '17:00',
  // Optional -- links this task to one of the chosen project's own
  // Design activities, so closing every task linked to it can auto-close
  // the activity (see project_service.maybe_auto_close_design_activity).
  selectedActivityId: '',
})
const isSubmitting = ref(false)

const { errors, setRules, validateAll } = useFormValidation()

setRules({
  title: [validators.required(t('task.formDialog.titleRequired'))],
  projectId: [validators.required(t('task.formDialog.projectRequired'))],
  assignedTo: [validators.required(t('task.formDialog.assigneeRequired'))],
  dueDate: [validators.required(t('task.formDialog.dueDateRequired'))],
  startDate: [
    () => !form.startDate || !form.dueDate || form.startDate <= form.dueDate || t('task.formDialog.startDateAfterDueDate'),
  ],
})

// Same "highlight empty mandatory fields immediately" behaviour as the
// Client/Project wizards (see NewClientWizardPage.vue's basicInfoErrors/
// etc) -- `errors` isn't only populated after a failed "Create Task"
// click, so Title/Project/Assign To/Completion Date are already flagged
// red the moment the page opens, before anything is typed or clicked.
function revalidate(): void {
  validateAll(form)
}
watch(form, revalidate, { deep: true, immediate: true })

const availableProjects = computed(() => {
  if (isProjectLocked.value) {
    return taskStore.projects.filter((project) => project.id === queryProjectId.value)
  }
  return taskStore.projects
})

const projectOptions = computed<SelectOption[]>(() =>
  availableProjects.value.map((project) => ({ label: project.projectName, value: project.id })),
)

const selectedProject = computed(() => taskStore.projects.find((project) => project.id === form.projectId))

const designActivityOptions = computed<SelectOption[]>(() =>
  (selectedProject.value?.selectedActivities ?? [])
    .filter((activity) => activity.id)
    .map((activity) => ({ label: activity.activityName, value: activity.id as string })),
)

// Every task must belong to exactly one project, and through it, one
// client -- resolving and showing the client here (read-only) as soon
// as a project is picked makes that tagging visible to whoever is
// creating the task, rather than leaving the client implicit.
const selectedClientName = computed<string | undefined>(() => {
  const project = taskStore.projects.find((item) => item.id === form.projectId)
  if (!project) return undefined
  return clientStore.getClientById(project.clientId)?.companyName ?? t('task.formDialog.unknownClient')
})

const assigneeOptions = computed<SelectOption[]>(() =>
  userStore.users
    .filter((user) => user.status === 'Active')
    .map((user) => ({
      label: user.id === authStore.user?.id ? t('task.formDialog.assigneeMe', { name: user.name }) : user.name,
      value: user.id,
    })),
)

function goBack(): void {
  if (isProjectLocked.value && queryProjectId.value) {
    router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId: queryProjectId.value } })
    return
  }
  router.push({ name: ROUTE_NAMES.TASKS })
}

async function submitTask(): Promise<void> {
  if (!validateAll(form)) return

  isSubmitting.value = true
  try {
    const task = await taskStore.createTask({
      projectId: form.projectId,
      title: form.title.trim(),
      assignedTo: form.assignedTo,
      priority: form.priority,
      severity: form.severity,
      startDate: form.startDate || undefined,
      dueDate: form.dueDate,
      dueTime: form.dueTime,
      status: 'Pending',
      selectedActivityId: form.selectedActivityId || undefined,
    })
    toastStore.show('success', t('task.taskActions.taskCreatedTitle'), t('task.taskActions.taskCreatedDescription', { title: task.title, assignee: task.assignedTo }))
    router.push({ name: ROUTE_NAMES.TASK_WORKSPACE, params: { taskId: task.id } })
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('task.taskActions.failedToCreateTask'), detail)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <BaseButton variant="ghost" size="sm" :icon="backIcon" class="self-start no-print" @click="goBack">
      {{ isProjectLocked ? t('task.workspace.backToProject') : t('task.workspace.backToTasks') }}
    </BaseButton>

    <div class="rounded-xl border border-border-light bg-bg-card p-5">
      <h1 class="mb-4 text-lg font-semibold text-text-primary">{{ t('task.formDialog.title') }}</h1>

      <div class="flex flex-col gap-4">
        <TextInput
          v-model="form.title"
          :label="t('task.formDialog.taskTitle')"
          :placeholder="t('task.formDialog.taskTitlePlaceholder')"
          required
          :error="errors.title"
        />

        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <div>
            <SelectBox
              v-model="form.projectId"
              :label="t('task.formDialog.project')"
              :placeholder="t('task.formDialog.projectPlaceholder')"
              :options="projectOptions"
              required
              :disabled="isProjectLocked"
              :error="errors.projectId"
            />
            <p v-if="selectedClientName" class="mt-1.5 text-xs text-text-muted">{{ t('task.formDialog.client', { name: selectedClientName }) }}</p>
          </div>

          <SelectBox
            :model-value="form.assignedTo"
            :label="t('task.formDialog.assignTo')"
            :options="assigneeOptions"
            required
            :error="errors.assignedTo"
            @update:model-value="form.assignedTo = $event"
          />
        </div>

        <SelectBox
          v-if="designActivityOptions.length > 0"
          v-model="form.selectedActivityId"
          :label="t('task.formDialog.designActivity')"
          :placeholder="t('task.formDialog.designActivityPlaceholder')"
          :options="designActivityOptions"
        />

        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
          <DatePicker v-model="form.startDate" :label="t('task.formDialog.startDate')" :max="form.dueDate || undefined" :error="errors.startDate" />
          <DatePicker v-model="form.dueDate" :label="t('task.formDialog.completionDate')" required :min="form.startDate || undefined" :error="errors.dueDate" />
          <TimePicker v-model="form.dueTime" :label="t('task.formDialog.completionTime')" required />
        </div>
      </div>

      <div class="mt-6 flex justify-end gap-3">
        <BaseButton variant="secondary" @click="goBack">{{ t('common.cancel') }}</BaseButton>
        <BaseButton :loading="isSubmitting" @click="submitTask">{{ t('task.formDialog.createTask') }}</BaseButton>
      </div>
    </div>
  </div>
</template>
