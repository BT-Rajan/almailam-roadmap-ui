<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter, useRoute, RouterLink } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import FormSection from '@/components/common/FormSection.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import RadioGroup from '@/components/common/RadioGroup.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import Stepper from '@/components/common/Stepper.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { PROJECT_SERVICES } from '@/constants/projectOptions'
import { useFormValidation } from '@/composables/useFormValidation'
import { useProjectStore } from '@/stores/projectStore'
import { useToastStore } from '@/stores/toastStore'
import { useUserStore } from '@/stores/userStore'
import type { Project, ProjectPriority } from '@/types/Project'
import type { SelectOption } from '@/types/Ui'
import { formatDate } from '@/utils/dateFormatter'
import { getProjectPriorityVariant } from '@/utils/projectHelpers'
import { validators } from '@/utils/validators'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()
const toastStore = useToastStore()
const userStore = useUserStore()

const WIZARD_STEPS = [
  { label: 'Client & Service' },
  { label: 'Project Details' },
  { label: 'Review & Confirm' },
]

const PRIORITY_OPTIONS: SelectOption[] = [
  { label: 'High', value: 'High' },
  { label: 'Medium', value: 'Medium' },
  { label: 'Low', value: 'Low' },
]

const currentStep = ref(0)
const isSubmitting = ref(false)
const showConfirmation = ref(false)
const createdProject = ref<Project | null>(null)

const form = reactive({
  clientId: '',
  service: '',
  engineer: '',
  priority: 'Medium' as ProjectPriority,
  projectName: '',
  scope: '',
  startDate: '',
  targetDate: '',
})

const { errors, setRules, validateAll } = useFormValidation()

setRules({
  clientId: [validators.required('Please select a client')],
  service: [validators.required('Please select a service')],
  engineer: [validators.required('Please assign an engineer')],
  projectName: [validators.required('Project name is required'), validators.minLength(5)],
  startDate: [validators.required('Start date is required')],
  targetDate: [validators.required('Target date is required')],
})

const clientOptions = ref<SelectOption[]>([])
const hasIneligibleClients = ref(false)
const serviceOptions: SelectOption[] = PROJECT_SERVICES.map((service) => ({ label: service, value: service }))
const engineerOptions = ref<SelectOption[]>([])

onMounted(async () => {
  if (projectStore.clients.length === 0) {
    await projectStore.loadProjects()
  }
  // Only clients that have completed onboarding AND are still Active can
  // have a project created for them (enforced server-side too, in
  // project_service.create_project) -- a project needs a real, currently
  // active client relationship behind it, not one still mid-onboarding
  // or one the business has since deactivated.
  const readyClients = projectStore.clients.filter(
    (client) => client.onboardingState === 'Ready' && client.status === 'Active',
  )
  hasIneligibleClients.value = readyClients.length < projectStore.clients.length
  clientOptions.value = readyClients.map((client) => ({ label: client.companyName, value: client.id }))

  // Arriving from a client's own workspace page ("New Project" there)
  // pre-selects that client -- saves a step and rules out picking the
  // wrong one out of a long list. Only pre-fills if the client is
  // actually eligible (Ready + Active); if not, the wizard's own
  // "No eligible clients" / ineligible-clients messaging below still
  // explains why, rather than silently pre-selecting something invalid.
  const preselectedClientId = route.query.clientId
  if (typeof preselectedClientId === 'string' && clientOptions.value.some((option) => option.value === preselectedClientId)) {
    form.clientId = preselectedClientId
  }

  if (userStore.users.length === 0) {
    await userStore.loadUsers()
  }
  engineerOptions.value = userStore.users
    .filter((user) => user.role === 'Engineer' && user.status === 'Active')
    .map((user) => ({ label: user.name, value: user.id }))
})

const STEP_FIELDS: Record<number, (keyof typeof form)[]> = {
  0: ['clientId', 'service', 'engineer'],
  1: ['projectName', 'startDate', 'targetDate'],
}

function validateStep(step: number): boolean {
  const fields = STEP_FIELDS[step]
  if (!fields) return true

  const data: Record<string, unknown> = {}
  fields.forEach((field) => {
    data[field] = form[field]
  })
  return validateAll(data)
}

function goNext(): void {
  if (!validateStep(currentStep.value)) return
  currentStep.value = Math.min(currentStep.value + 1, WIZARD_STEPS.length - 1)
}

function goBack(): void {
  currentStep.value = Math.max(currentStep.value - 1, 0)
}

function cancelWizard(): void {
  router.push({ name: ROUTE_NAMES.PROJECTS })
}

function selectedClientName(): string {
  return projectStore.clients.find((client) => client.id === form.clientId)?.companyName ?? 'Not selected'
}

function selectedEngineerName(): string {
  return userStore.users.find((user) => user.id === form.engineer)?.name ?? 'Not selected'
}

async function submitWizard(): Promise<void> {
  if (!validateStep(0) || !validateStep(1)) {
    currentStep.value = 0
    return
  }

  isSubmitting.value = true

  try {
    const project = await projectStore.createProject({
      projectName: form.projectName,
      description: form.scope || undefined,
      clientId: form.clientId,
      service: form.service,
      engineerId: form.engineer,
      priority: form.priority,
      startDate: form.startDate,
      targetDate: form.targetDate,
    })

    toastStore.show('success', 'Project created', `${project.projectName} was added to the pipeline.`)
    createdProject.value = project
    showConfirmation.value = true
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please check the form and try again.'
    toastStore.show('error', 'Failed to create project', detail)
  } finally {
    isSubmitting.value = false
  }
}

function goToCreatedProject(): void {
  if (!createdProject.value) return
  showConfirmation.value = false
  router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId: createdProject.value.id } })
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader title="New Project Wizard" subtitle="Set up a new engineering consulting engagement in a few steps." />

    <div class="rounded-xl border border-border-light bg-bg-card p-6">
      <Stepper :steps="WIZARD_STEPS" :current-step="currentStep" />

      <div class="mt-8">
        <FormSection
          v-if="currentStep === 0"
          title="Client & Service"
          description="Choose the client this engagement is for and the service being delivered."
        >
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <div class="flex flex-col gap-1.5">
              <SelectBox
                v-model="form.clientId"
                label="Client"
                placeholder="Select a client"
                required
                :options="clientOptions"
                :error="errors.clientId"
              />
              <p v-if="clientOptions.length === 0" class="text-xs text-warning-600">
                No eligible clients found. A client must have completed onboarding ("Ready") and be Active before a project can be created for them.
              </p>
              <p v-else-if="hasIneligibleClients" class="text-xs text-neutral-400">
                Only clients that are Active and have completed onboarding are shown.
              </p>
              <RouterLink :to="{ name: ROUTE_NAMES.CLIENT_NEW }" class="self-start text-xs font-medium text-primary-600 hover:text-primary-700">
                + Onboard a new client
              </RouterLink>
            </div>
            <SelectBox
              v-model="form.service"
              label="Service"
              placeholder="Select a service"
              required
              :options="serviceOptions"
              :error="errors.service"
            />
            <SelectBox
              v-model="form.engineer"
              label="Responsible Engineer"
              placeholder="Assign an engineer"
              required
              :options="engineerOptions"
              :error="errors.engineer"
            />
            <RadioGroup v-model="form.priority" label="Priority" :options="PRIORITY_OPTIONS" :vertical="false" />
          </div>
        </FormSection>

        <FormSection
          v-else-if="currentStep === 1"
          title="Project Details"
          description="Describe the engagement and set the delivery timeline."
        >
          <TextInput
            v-model="form.projectName"
            label="Project Name"
            placeholder="e.g. Al Reem Residential Tower - Structural Design"
            required
            :error="errors.projectName"
          />
          <TextArea v-model="form.scope" label="Scope of Work" placeholder="Describe the scope of this engagement" :rows="4" />
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <DatePicker v-model="form.startDate" label="Start Date" required :error="errors.startDate" />
            <DatePicker v-model="form.targetDate" label="Target Completion Date" required :error="errors.targetDate" />
          </div>
        </FormSection>

        <FormSection v-else title="Review & Confirm" description="Confirm the details before creating the project.">
          <div class="grid grid-cols-1 gap-x-8 gap-y-4 tablet:grid-cols-2">
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Client</p>
              <p class="text-sm text-neutral-800">{{ selectedClientName() }}</p>
            </div>
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Service</p>
              <p class="text-sm text-neutral-800">{{ form.service || 'Not selected' }}</p>
            </div>
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Responsible Engineer</p>
              <p class="text-sm text-neutral-800">{{ selectedEngineerName() }}</p>
            </div>
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Priority</p>
              <StatusBadge :label="form.priority" :variant="getProjectPriorityVariant(form.priority)" />
            </div>
            <div class="tablet:col-span-2">
              <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Project Name</p>
              <p class="text-sm text-neutral-800">{{ form.projectName || 'Not entered' }}</p>
            </div>
            <div v-if="form.scope" class="tablet:col-span-2">
              <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Scope of Work</p>
              <p class="text-sm text-neutral-800">{{ form.scope }}</p>
            </div>
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Start Date</p>
              <p class="text-sm text-neutral-800">{{ form.startDate ? formatDate(form.startDate) : 'Not set' }}</p>
            </div>
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Target Date</p>
              <p class="text-sm text-neutral-800">{{ form.targetDate ? formatDate(form.targetDate) : 'Not set' }}</p>
            </div>
          </div>
        </FormSection>
      </div>

      <div class="mt-8 flex items-center justify-between border-t border-border-light pt-4">
        <FormActionBar
          v-if="currentStep === 0"
          cancel-label="Cancel"
          submit-label="Next"
          @cancel="cancelWizard"
          @submit="goNext"
        />
        <FormActionBar
          v-else-if="currentStep < WIZARD_STEPS.length - 1"
          cancel-label="Back"
          submit-label="Next"
          @cancel="goBack"
          @submit="goNext"
        />
        <FormActionBar
          v-else
          cancel-label="Back"
          submit-label="Create Project"
          :loading="isSubmitting"
          @cancel="goBack"
          @submit="submitWizard"
        />
      </div>
    </div>

    <BaseDialog :model-value="showConfirmation" title="Project Created" size="sm" :closable="false">
      <p class="text-sm text-neutral-600">
        <strong>{{ createdProject?.projectName }}</strong>
        was successfully created as project
        <strong>{{ createdProject?.projectNo }}</strong>
        for <strong>{{ selectedClientName() }}</strong>.
      </p>

      <template #footer>
        <BaseButton variant="primary" @click="goToCreatedProject">View Project Workspace</BaseButton>
      </template>
    </BaseDialog>
  </div>
</template>
