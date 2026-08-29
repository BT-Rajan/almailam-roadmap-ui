<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter, useRoute, RouterLink } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import FormSection from '@/components/common/FormSection.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import RadioGroup from '@/components/common/RadioGroup.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import PermitPickerDialog from '@/components/project/PermitPickerDialog.vue'
import ServicePickerDialog from '@/components/project/ServicePickerDialog.vue'
import TypeActivityPickerDialog from '@/components/project/TypeActivityPickerDialog.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import Stepper from '@/components/common/Stepper.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useFormValidation } from '@/composables/useFormValidation'
import { usePermitCatalogStore } from '@/stores/permitCatalogStore'
import { useProjectStore } from '@/stores/projectStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import { useServiceCatalogStore } from '@/stores/serviceCatalogStore'
import { useTaskStore } from '@/stores/taskStore'
import { useToastStore } from '@/stores/toastStore'
import { useTypeActivityCatalogStore } from '@/stores/typeActivityCatalogStore'
import { useUserStore } from '@/stores/userStore'
import type { PermitCatalogItem } from '@/types/PermitCatalog'
import type { Project, ProjectPriority } from '@/types/Project'
import type { SelectedServiceActivity } from '@/types/ServiceCatalog'
import type { SelectedTypeActivity } from '@/types/TypeActivityCatalog'
import type { SelectOption } from '@/types/Ui'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { getProjectPriorityVariant } from '@/utils/projectHelpers'
import { validators } from '@/utils/validators'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()
const resultDialogStore = useResultDialogStore()
const toastStore = useToastStore()
const userStore = useUserStore()
const serviceCatalogStore = useServiceCatalogStore()
const permitCatalogStore = usePermitCatalogStore()
const typeActivityCatalogStore = useTypeActivityCatalogStore()
const taskStore = useTaskStore()

const WIZARD_STEPS = [
  { label: 'Client & Service' },
  { label: 'Project Details' },
  { label: 'Permits' },
  { label: 'Additional Services' },
  { label: 'Review & Confirm' },
]

const PRIORITY_OPTIONS: SelectOption[] = [
  { label: 'High', value: 'High' },
  { label: 'Medium', value: 'Medium' },
  { label: 'Low', value: 'Low' },
]

const YES_NO_OPTIONS: SelectOption[] = [
  { label: 'Yes', value: 'yes' },
  { label: 'No', value: 'no' },
]

interface WizardPermit {
  // The permit catalog item's id -- picked via PermitPickerDialog, same
  // as SelectedServiceActivity keys off catalog ids rather than a
  // locally generated one.
  id: string
  name: string
  // '' means not yet answered -- required before the step can advance.
  clientHas: 'yes' | 'no' | ''
}

const currentStep = ref(0)
const isSubmitting = ref(false)
const showConfirmation = ref(false)
const createdProject = ref<Project | null>(null)
const isServicePickerOpen = ref(false)
const isPermitPickerOpen = ref(false)
const isTypeActivityPickerOpen = ref(false)

const form = reactive({
  clientId: '',
  // Kept as a comma-joined summary of the distinct services in
  // selectedActivities below -- this is what actually gets sent as
  // Project.service and is what every existing display spot (workspace
  // header, review step, etc.) reads. Derived, not user-editable directly.
  service: '',
  selectedActivities: [] as SelectedServiceActivity[],
  engineer: '',
  priority: 'Medium' as ProjectPriority,
  projectName: '',
  scope: '',
  startDate: '',
  targetDate: '',
  // '' until answered; drives whether the permit picker below is shown.
  involvesPermits: '' as 'yes' | 'no' | '',
  permits: [] as WizardPermit[],
  // The final wizard step's picks -- one engagement type category (or
  // none, if skipped) plus whichever of its activities were checked.
  // Coverage against selectedActivities above is computed server-side
  // at creation time, not here (see project_service._resolve_type_
  // activity_selection) -- the wizard just sends what was checked.
  selectedTypeActivities: [] as SelectedTypeActivity[],
})

// Confirming the picker replaces the whole selection, same as
// ServicePickerDialog -- existing picks keep whatever clientHas answer
// was already given, newly added ones start unanswered.
function handlePermitsConfirm(selected: PermitCatalogItem[]): void {
  const existingById = new Map(form.permits.map((permit) => [permit.id, permit]))
  form.permits = selected.map((permit) => ({
    id: permit.id,
    name: permit.name,
    clientHas: existingById.get(permit.id)?.clientHas ?? '',
  }))
}

function removePermit(id: string): void {
  form.permits = form.permits.filter((permit) => permit.id !== id)
}

// Confirming the picker replaces the whole selection -- same "whole
// selection, not merge" convention as handleServicesConfirmed/
// handlePermitsConfirm above.
function handleTypeActivitiesConfirm(selected: SelectedTypeActivity[]): void {
  form.selectedTypeActivities = selected
}

function removeTypeActivity(activityId: string): void {
  form.selectedTypeActivities = form.selectedTypeActivities.filter((item) => item.activityId !== activityId)
}

// Distinct category names among what's checked, in selection order --
// e.g. "Design, Supervision" once picking spans more than one category.
const selectedTypeActivityCategoryNames = computed(() =>
  [...new Set(form.selectedTypeActivities.map((item) => item.categoryName))].join(', '),
)

// Scope of Work is auto-populated from whatever was picked in the
// service picker and the type-activity picker -- "scope = services +
// activities", per the actual requirement, rather than staff retyping
// a summary of choices already made elsewhere in this same wizard.
// Still a normal editable TextArea: lastAutoScope tracks the most
// recent auto-generated text so a manual edit (form.scope diverging
// from it) is respected and stops being overwritten -- otherwise
// picking one more activity after typing a custom scope would silently
// discard what staff just wrote.
const lastAutoScope = ref('')

function buildScopeText(): string {
  const lines: string[] = []
  const activitiesByService = new Map<string, string[]>()
  for (const item of form.selectedActivities) {
    const list = activitiesByService.get(item.serviceName) ?? []
    list.push(item.activityId === item.serviceId ? item.serviceName : item.activityName)
    activitiesByService.set(item.serviceName, list)
  }
  for (const [serviceName, activityNames] of activitiesByService) {
    lines.push(`${serviceName}:`)
    activityNames.forEach((name) => lines.push(`- ${name}`))
  }
  const typeActivitiesByCategory = new Map<string, string[]>()
  for (const item of form.selectedTypeActivities) {
    const list = typeActivitiesByCategory.get(item.categoryName) ?? []
    list.push(item.activityName)
    typeActivitiesByCategory.set(item.categoryName, list)
  }
  for (const [categoryName, activityNames] of typeActivitiesByCategory) {
    if (lines.length > 0) lines.push('')
    lines.push(`${categoryName} Activities:`)
    activityNames.forEach((name) => lines.push(`- ${name}`))
  }
  return lines.join('\n')
}

watch(
  () => [form.selectedActivities, form.selectedTypeActivities],
  () => {
    const generated = buildScopeText()
    if (form.scope.trim().length === 0 || form.scope === lastAutoScope.value) {
      form.scope = generated
      lastAutoScope.value = generated
    }
  },
  { deep: true },
)

const serviceTotal = computed(() => form.selectedActivities.reduce((sum, item) => sum + item.fixedCost, 0))

const { errors, setRules, validateAll } = useFormValidation()

setRules({
  clientId: [validators.required('Please select a client')],
  selectedActivities: [validators.required('Please select at least one service')],
  engineer: [validators.required('Please assign an engineer')],
  projectName: [validators.required('Project name is required'), validators.minLength(5)],
  startDate: [validators.required('Start date is required')],
  targetDate: [validators.required('Target date is required')],
})

function handleServicesConfirmed(items: SelectedServiceActivity[]): void {
  form.selectedActivities = items
  form.service = [...new Set(items.map((item) => item.serviceName))].join(', ')
}

const clientOptions = ref<SelectOption[]>([])
const hasIneligibleClients = ref(false)
const engineerOptions = ref<SelectOption[]>([])

onMounted(async () => {
  // Always fetch fresh -- not guarded by `if (projectStore.clients.length
  // === 0)` the way this used to be. That guard meant the eligible-clients
  // list was only ever fetched once per session: if projectStore.clients
  // had been populated at any earlier point (visiting the Projects list,
  // etc.), it was never refreshed here, so a client who completed
  // onboarding *after* that earlier fetch would silently never appear as
  // eligible -- the exact real-world sequence of "onboard a client, then
  // immediately try to create a project for them" that this page exists
  // for. Eligibility is a correctness question; it can't be served from
  // a cache that might be from before the thing being checked changed.
  await projectStore.loadProjects()

  // Services (and their activities/prices) come from the admin-configurable
  // catalog (Administration > Service Catalog) and feed the service picker
  // dialog directly, so anything added there shows up here without a code
  // change. Fetched fresh for the same reason as the client list above.
  await serviceCatalogStore.loadServices()
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

  // Backs the permit picker below -- loaded once here rather than
  // lazily on first dialog open so the list is ready immediately.
  if (permitCatalogStore.permits.length === 0) {
    await permitCatalogStore.loadPermits()
  }

  // Backs the type activity picker (final wizard step) -- same
  // "load once here" reasoning as the permit catalog above.
  if (typeActivityCatalogStore.categories.length === 0) {
    await typeActivityCatalogStore.loadCategories()
  }
})

const STEP_FIELDS: Record<number, (keyof typeof form)[]> = {
  0: ['clientId', 'selectedActivities', 'engineer'],
  1: ['projectName', 'startDate', 'targetDate'],
}

function validateStep(step: number): boolean {
  // Step 2 (Permits) is informational only -- it's never allowed to
  // block moving on or creating the project, regardless of whether
  // "involves permits" was answered or every listed permit has a
  // client-has answer.
  if (step === 2) return true

  const fields = STEP_FIELDS[step]
  if (!fields) return true

  const data: Record<string, unknown> = {}
  fields.forEach((field) => {
    data[field] = form[field]
  })
  return validateAll(data)
}

function goNext(): void {
  if (!validateStep(currentStep.value)) {
    // Previously a silent no-op: the button just did nothing, with the
    // only sign anything was wrong being red text under a field that
    // might be scrolled out of view -- easy to read as "this isn't
    // working" rather than "something needs fixing here."
    toastStore.show(
      'error',
      'Please fix the highlighted fields',
      `Some fields under "${WIZARD_STEPS[currentStep.value].label}" need attention before continuing.`,
    )
    return
  }
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
  // Re-entrancy guard, checked first and synchronously: the submit
  // button's own :disabled="isSubmitting" doesn't fully prevent a
  // double-submit -- Vue applies that to the DOM asynchronously (its
  // own render scheduler), so a fast double-click (or an impatient
  // second click while the network request is in flight) can fire this
  // handler a second time before the button visually disables. Without
  // this, that second call ran the same create request again --
  // duplicate projects, duplicate permit tasks, and a confirmation
  // dialog that ended up reflecting whichever call finished last rather
  // than clearly confirming the one thing that was asked for.
  if (isSubmitting.value) return

  // Previously silent: this could send someone from the Review step
  // straight back to step 0 with no toast and no explanation, easy to
  // read as "the button didn't do anything" rather than "something on
  // an earlier step needs fixing." Re-validating on submit (not just on
  // each Next) catches a step broken after the fact -- e.g. jumping
  // back via the stepper and clearing a field -- so it can't be skipped.
  if (!validateStep(0) || !validateStep(1)) {
    toastStore.show(
      'error',
      'Please fix the highlighted fields',
      "Some earlier fields need attention before this project can be created.",
    )
    currentStep.value = 0
    return
  }

  isSubmitting.value = true

  try {
    const permitsClientHas = form.permits.filter((permit) => permit.clientHas === 'yes').map((permit) => permit.name)
    const permitsClientLacks = form.permits.filter((permit) => permit.clientHas === 'no').map((permit) => permit.name)

    // Optional step -- only sent when something was actually checked, so
    // an unaware/older backend (or simply a project that skipped this
    // step) doesn't get an empty/meaningless selection object.
    const typeActivitySelection =
      form.selectedTypeActivities.length > 0
        ? { activityIds: form.selectedTypeActivities.map((activity) => activity.activityId) }
        : undefined

    const project = await projectStore.createProject({
      projectName: form.projectName,
      description: form.scope || undefined,
      clientId: form.clientId,
      service: form.service,
      selectedActivities: form.selectedActivities,
      serviceTotal: serviceTotal.value,
      engineerId: form.engineer,
      priority: form.priority,
      startDate: form.startDate,
      targetDate: form.targetDate,
      // Permits the client already holds become a mandatory upload
      // checklist on the project's Documents tab.
      requiredPermitDocuments: permitsClientHas.length > 0 ? permitsClientHas : undefined,
      typeActivitySelection,
    })

    // Permits the client doesn't have yet aren't a document to chase --
    // they're work to do, so each becomes a task on the project instead.
    if (permitsClientLacks.length > 0) {
      const results = await Promise.allSettled(
        permitsClientLacks.map((permitName) =>
          taskStore.createTask({
            projectId: project.id,
            title: `Obtain permit: ${permitName}`,
            assignedTo: form.engineer,
            priority: form.priority,
            severity: 'Major',
            dueDate: form.targetDate,
            dueTime: '17:00',
            status: 'Pending',
          }),
        ),
      )
      const failedCount = results.filter((result) => result.status === 'rejected').length
      if (failedCount > 0) {
        toastStore.show(
          'error',
          'Some permit tasks were not created',
          `${failedCount} of ${permitsClientLacks.length} permit task(s) failed -- add them manually from the Tasks tab.`,
        )
      }
    }

    toastStore.show('success', 'Project created', `${project.projectName} was added to the pipeline.`)
    createdProject.value = project
    showConfirmation.value = true
  } catch (error) {
    // An explicit, must-acknowledge dialog rather than a toast -- same
    // reasoning as every other create-style wizard in the app (see
    // NewClientWizardPage.vue): a toast auto-dismisses in 4 seconds, so
    // a failure here could come and go while attention was on the form
    // (or the confirmation that never appeared), reading as "nothing
    // happened" rather than "this needs a fix."
    const detail = error instanceof Error && error.message ? error.message : 'Please check the form and try again.'
    resultDialogStore.showError('Failed to create project', detail)
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
              <p v-else-if="hasIneligibleClients" class="text-xs text-text-muted">
                Only clients that are Active and have completed onboarding are shown.
              </p>
              <RouterLink :to="{ name: ROUTE_NAMES.CLIENT_NEW }" class="self-start text-xs font-medium text-primary-600 hover:text-primary-700">
                + Onboard a new client
              </RouterLink>
            </div>
            <div class="flex flex-col gap-1.5">
              <label id="service-picker-label" class="text-sm font-medium text-text-secondary">Service <span class="text-danger-500">*</span></label>
              <button
                id="service-picker-button"
                type="button"
                aria-labelledby="service-picker-label service-picker-button"
                class="flex min-h-[42px] w-full items-center justify-between rounded-lg border bg-bg-card px-3 py-2 text-left text-sm transition-colors duration-fast hover:bg-bg-hover"
                :class="errors.selectedActivities ? 'border-danger-500' : 'border-border-default'"
                @click="isServicePickerOpen = true"
              >
                <span v-if="form.selectedActivities.length === 0" class="text-text-muted">Select a service</span>
                <span v-else class="text-text-primary">
                  {{ form.selectedActivities.length }} activit{{ form.selectedActivities.length === 1 ? 'y' : 'ies' }} ·
                  {{ formatCurrency(serviceTotal, 'KWD') }}
                </span>
                <span class="text-xs font-medium text-primary-600">{{ form.selectedActivities.length === 0 ? 'Choose' : 'Edit' }}</span>
              </button>
              <p v-if="errors.selectedActivities" class="text-xs text-danger-600">{{ errors.selectedActivities }}</p>
              <p v-else-if="form.selectedActivities.length > 0" class="truncate text-xs text-text-muted">{{ form.service }}</p>
            </div>
            <SelectBox
              v-model="form.engineer"
              label="Field Engineer"
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
          <TextArea
            v-model="form.scope"
            label="Scope of Work"
            placeholder="Describe the scope of this engagement"
            hint="Auto-filled from the services and additional activities picked earlier -- edit freely if it needs adjusting."
            :rows="6"
          />
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <DatePicker v-model="form.startDate" label="Start Date" required :error="errors.startDate" />
            <DatePicker v-model="form.targetDate" label="Target Completion Date" required :error="errors.targetDate" />
          </div>
        </FormSection>

        <FormSection
          v-else-if="currentStep === 2"
          title="Permits"
          description="Capture any permits this project needs and whether the client already holds them."
        >
          <RadioGroup
            v-model="form.involvesPermits"
            label="Does this project involve any permits?"
            :options="YES_NO_OPTIONS"
            :vertical="false"
          />

          <template v-if="form.involvesPermits === 'yes'">
            <div class="flex flex-col gap-1.5">
              <label id="permits-picker-label" class="text-sm font-medium text-text-secondary">Permits <span class="text-danger-500">*</span></label>
              <button
                id="permits-picker-button"
                type="button"
                aria-labelledby="permits-picker-label permits-picker-button"
                class="flex min-h-[42px] w-full items-center justify-between rounded-lg border border-border-default bg-bg-card px-3 py-2 text-left text-sm transition-colors duration-fast hover:bg-bg-hover"
                @click="isPermitPickerOpen = true"
              >
                <span v-if="form.permits.length === 0" class="text-text-muted">Select permits</span>
                <span v-else class="text-text-primary">
                  {{ form.permits.length }} permit{{ form.permits.length === 1 ? '' : 's' }} selected
                </span>
                <span class="text-xs font-medium text-primary-600">{{ form.permits.length === 0 ? 'Choose' : 'Edit' }}</span>
              </button>
            </div>

            <div v-if="form.permits.length > 0" class="flex flex-col gap-2">
              <div
                v-for="permit in form.permits"
                :key="permit.id"
                class="flex flex-col gap-2 rounded-lg border border-border-light p-3 tablet:flex-row tablet:items-center tablet:justify-between"
              >
                <span class="text-sm font-medium text-text-primary">{{ permit.name }}</span>

                <div class="flex items-center gap-3">
                  <RadioGroup
                    :model-value="permit.clientHas"
                    :options="YES_NO_OPTIONS"
                    :vertical="false"
                    @update:model-value="permit.clientHas = $event as 'yes' | 'no'"
                  />
                  <button
                    type="button"
                    class="text-xs font-medium text-danger-600 hover:text-danger-700"
                    :aria-label="`Remove ${permit.name}`"
                    @click="removePermit(permit.id)"
                  >
                    Remove
                  </button>
                </div>
              </div>
              <p class="text-xs text-text-muted">
                Permits the client already has will be required uploads in the Documents tab. Permits the client
                doesn't have yet will be added as tasks.
              </p>
            </div>
          </template>
        </FormSection>

        <FormSection
          v-else-if="currentStep === 3"
          title="Additional Services"
          description="Pick an engagement type and check off which of its activities apply -- anything not already covered by the services picked earlier adds its own cost to the quotation."
        >
          <div class="flex flex-col gap-1.5">
            <label id="type-activity-picker-label" class="text-sm font-medium text-text-secondary">Additional Services</label>
            <button
              id="type-activity-picker-button"
              type="button"
              aria-labelledby="type-activity-picker-label type-activity-picker-button"
              class="flex min-h-[42px] w-full items-center justify-between rounded-lg border border-border-default bg-bg-card px-3 py-2 text-left text-sm transition-colors duration-fast hover:bg-bg-hover"
              @click="isTypeActivityPickerOpen = true"
            >
              <span v-if="form.selectedTypeActivities.length === 0" class="text-text-muted">Select additional services (optional)</span>
              <span v-else class="text-text-primary">
                {{ form.selectedTypeActivities.length }} activit{{ form.selectedTypeActivities.length === 1 ? 'y' : 'ies' }} selected ·
                {{ selectedTypeActivityCategoryNames }}
              </span>
              <span class="text-xs font-medium text-primary-600">{{ form.selectedTypeActivities.length === 0 ? 'Choose' : 'Edit' }}</span>
            </button>
            <p class="text-xs text-text-muted">
              This step is optional -- skip it if the engagement doesn't need a Design/Supervision/etc breakdown on top
              of the services already picked.
            </p>
          </div>

          <div v-if="form.selectedTypeActivities.length > 0" class="flex flex-col gap-2">
            <div
              v-for="activity in form.selectedTypeActivities"
              :key="activity.activityId"
              class="flex items-center justify-between gap-3 rounded-lg border border-border-light p-3"
            >
              <div class="min-w-0">
                <p class="truncate text-sm font-medium text-text-primary">{{ activity.activityName }}</p>
                <p class="truncate text-xs text-text-muted">{{ activity.categoryName }} · {{ formatCurrency(activity.cost) }}</p>
              </div>
              <button
                type="button"
                class="shrink-0 text-xs font-medium text-danger-600 hover:text-danger-700"
                :aria-label="`Remove ${activity.activityName}`"
                @click="removeTypeActivity(activity.activityId)"
              >
                Remove
              </button>
            </div>
          </div>
        </FormSection>

        <FormSection v-else title="Review & Confirm" description="Confirm the details before creating the project.">
          <div class="grid grid-cols-1 gap-x-8 gap-y-4 tablet:grid-cols-2">
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Client</p>
              <p class="text-sm text-text-primary">{{ selectedClientName() }}</p>
            </div>
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Service</p>
              <p class="text-sm text-text-primary">{{ form.service || 'Not selected' }}</p>
              <ul v-if="form.selectedActivities.length > 0" class="mt-1 flex flex-col gap-0.5">
                <li v-for="item in form.selectedActivities" :key="item.activityId" class="flex items-center justify-between gap-3 text-xs text-text-muted">
                  <span class="truncate">{{ item.activityName }}</span>
                  <span class="shrink-0">{{ formatCurrency(item.fixedCost, 'KWD') }}</span>
                </li>
                <li class="flex items-center justify-between gap-3 border-t border-border-light pt-1 text-xs font-medium text-text-secondary">
                  <span>Total</span>
                  <span>{{ formatCurrency(serviceTotal, 'KWD') }}</span>
                </li>
              </ul>
            </div>
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Field Engineer</p>
              <p class="text-sm text-text-primary">{{ selectedEngineerName() }}</p>
            </div>
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Priority</p>
              <StatusBadge :label="form.priority" :variant="getProjectPriorityVariant(form.priority)" />
            </div>
            <div class="tablet:col-span-2">
              <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Project Name</p>
              <p class="text-sm text-text-primary">{{ form.projectName || 'Not entered' }}</p>
            </div>
            <div v-if="form.scope" class="tablet:col-span-2">
              <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Scope of Work</p>
              <p class="text-sm text-text-primary">{{ form.scope }}</p>
            </div>
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Start Date</p>
              <p class="text-sm text-text-primary">{{ form.startDate ? formatDate(form.startDate) : 'Not set' }}</p>
            </div>
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Target Date</p>
              <p class="text-sm text-text-primary">{{ form.targetDate ? formatDate(form.targetDate) : 'Not set' }}</p>
            </div>
            <div class="tablet:col-span-2">
              <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Permits</p>
              <p v-if="form.involvesPermits !== 'yes' || form.permits.length === 0" class="text-sm text-text-primary">
                None
              </p>
              <ul v-else class="mt-1 flex flex-col gap-0.5">
                <li v-for="permit in form.permits" :key="permit.id" class="flex items-center justify-between gap-3 text-xs text-text-secondary">
                  <span class="truncate">{{ permit.name }}</span>
                  <span class="shrink-0">{{ permit.clientHas === 'yes' ? 'Client has it -- mandatory upload' : 'Client needs it -- task will be created' }}</span>
                </li>
              </ul>
            </div>
            <div class="tablet:col-span-2">
              <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Additional Services</p>
              <p v-if="form.selectedTypeActivities.length === 0" class="text-sm text-text-primary">None</p>
              <template v-else>
                <p class="text-sm text-text-primary">{{ selectedTypeActivityCategoryNames }}</p>
                <ul class="mt-1 flex flex-col gap-0.5">
                  <li v-for="activity in form.selectedTypeActivities" :key="activity.activityId" class="flex items-center justify-between gap-3 text-xs text-text-muted">
                    <span class="truncate">{{ activity.activityName }}</span>
                    <span class="shrink-0">{{ formatCurrency(activity.cost) }}</span>
                  </li>
                </ul>
                <p class="mt-1 text-xs text-text-muted">
                  Activities already covered by the services picked earlier won't be charged again -- the final
                  additional amount is calculated once the project is created.
                </p>
              </template>
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

    <ServicePickerDialog
      v-model="isServicePickerOpen"
      :services="serviceCatalogStore.services"
      :selected="form.selectedActivities"
      currency="KWD"
      @confirm="handleServicesConfirmed"
    />

    <PermitPickerDialog
      v-model="isPermitPickerOpen"
      :permits="permitCatalogStore.permits"
      :selected-ids="form.permits.map((permit) => permit.id)"
      @confirm="handlePermitsConfirm"
    />

    <TypeActivityPickerDialog
      v-model="isTypeActivityPickerOpen"
      :categories="typeActivityCatalogStore.categories"
      :selected="form.selectedTypeActivities"
      currency="KWD"
      @confirm="handleTypeActivitiesConfirm"
    />

    <BaseDialog :model-value="showConfirmation" title="Project Created" size="sm" :closable="false">
      <p class="text-sm text-text-secondary">
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
