<script setup lang="ts">
import { computed, onMounted, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useFormValidation } from '@/composables/useFormValidation'
import { useServiceCatalogStore } from '@/stores/serviceCatalogStore'
import { useUserStore } from '@/stores/userStore'
import type { Project, ProjectPriority } from '@/types/Project'
import type { ProjectUpdateInput } from '@/services/projectService'
import type { SelectOption } from '@/types/Ui'
import { validators } from '@/utils/validators'

const props = defineProps<{
  modelValue: boolean
  project: Project
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: ProjectUpdateInput]
}>()

const { t } = useI18n()

const PRIORITY_OPTIONS: SelectOption[] = [
  { label: 'High', value: 'High', labelKey: 'project.priority.high' },
  { label: 'Medium', value: 'Medium', labelKey: 'project.priority.medium' },
  { label: 'Low', value: 'Low', labelKey: 'project.priority.low' },
]
const userStore = useUserStore()
const serviceCatalogStore = useServiceCatalogStore()
onMounted(() => {
  if (userStore.users.length === 0) userStore.loadUsers()
  if (serviceCatalogStore.services.length === 0) serviceCatalogStore.loadServices()
})

// Services come from the admin-configurable catalog (Administration >
// Service Catalog). If this project's current service was since removed
// from the catalog, it's still included here so the dropdown doesn't
// silently show a blank value for it.
const serviceOptions = computed<SelectOption[]>(() => {
  const names = new Set(serviceCatalogStore.services.map((service) => service.name))
  names.add(props.project.service)
  return [...names].map((name) => ({ label: name, value: name }))
})
// Every active staff member can be assigned, not only those with the
// Engineer role -- a Project Manager occasionally runs point on a
// project too, and this only reassigns responsibility, it doesn't grant
// or restrict any permission.
const engineerOptions = computed<SelectOption[]>(() =>
  userStore.users.filter((user) => user.status === 'Active').map((user) => ({ label: `${user.name} (${user.role})`, value: user.id })),
)

interface EditForm {
  projectName: string
  description: string
  siteAddress: string
  service: string
  priority: string
  targetDate: string
  engineerId: string
}

function emptyForm(): EditForm {
  return {
    projectName: '',
    description: '',
    siteAddress: '',
    service: '',
    priority: 'Medium',
    targetDate: '',
    engineerId: '',
  }
}

const form = reactive(emptyForm())
const { errors, setRules, validateAll } = useFormValidation()

setRules({
  projectName: [validators.required('Project name is required'), validators.minLength(5)],
  service: [validators.required('Please select a service')],
  engineerId: [validators.required('Please assign an engineer')],
  targetDate: [validators.required('Target date is required')],
})

watch(
  [() => props.modelValue, () => userStore.users.length],
  ([open]) => {
    if (!open) return
    form.projectName = props.project.projectName
    form.description = props.project.description ?? ''
    form.siteAddress = props.project.siteAddress ?? ''
    form.service = props.project.service
    form.priority = props.project.priority
    form.targetDate = props.project.targetDate
    // Project only stores the engineer's resolved display name, not
    // their id, so this is a best-effort match rather than a guaranteed
    // one -- but leaving it forced blank on every open (the previous
    // behaviour) meant staff had to re-select the engineer on every
    // single edit, even when they only wanted to change something else
    // entirely (progress, target date, ...). Since engineerId is a
    // required field, forgetting that one unrelated dropdown meant
    // "Save Changes" would silently fail validation -- from the outside
    // that looks exactly like "the edit dialog doesn't work", not like
    // a missing field. Also re-runs once userStore.users finishes
    // loading, in case the dialog was opened before that resolved.
    const currentEngineer = userStore.users.find((user) => user.name === props.project.engineer)
    form.engineerId = currentEngineer?.id ?? ''
  },
  { immediate: true },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  if (!validateAll(form)) return
  emit('confirm', {
    projectName: form.projectName,
    description: form.description,
    siteAddress: form.siteAddress,
    service: form.service,
    priority: form.priority as ProjectPriority,
    targetDate: form.targetDate,
    engineerId: form.engineerId,
  })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="t('project.editDialog.title')" size="lg" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <TextInput v-model="form.projectName" :label="t('project.editDialog.projectName')" required :error="errors.projectName" />
      <TextArea v-model="form.description" :label="t('project.editDialog.scopeOfWork')" :placeholder="t('project.editDialog.scopeOfWorkPlaceholder')" :rows="3" />
      <TextInput v-model="form.siteAddress" :label="t('project.editDialog.siteAddress')" :placeholder="t('project.editDialog.siteAddressPlaceholder')" />

      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <SelectBox v-model="form.service" :label="t('project.editDialog.service')" :options="serviceOptions" required :error="errors.service" />
        <SelectBox v-model="form.priority" :label="t('project.editDialog.priority')" :options="PRIORITY_OPTIONS" />
        <SelectBox
          v-model="form.engineerId"
          :label="t('project.editDialog.reassignEngineer')"
          :placeholder="t('project.editDialog.reassignEngineerPlaceholder')"
          :options="engineerOptions"
          required
          :error="errors.engineerId"
        />
        <DatePicker v-model="form.targetDate" :label="t('project.editDialog.targetCompletionDate')" required :error="errors.targetDate" />
      </div>

      <!-- Progress is no longer editable here -- it's computed from the
           execution-step checklist, not a number to slide by hand. -->
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">{{ t('common.saveChanges') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
