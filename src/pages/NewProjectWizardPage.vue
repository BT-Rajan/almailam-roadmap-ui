<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter, useRoute, RouterLink } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import FormSection from '@/components/common/FormSection.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import RadioGroup from '@/components/common/RadioGroup.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import ServicePickerDialog from '@/components/project/ServicePickerDialog.vue'
import type { ServicePickerConfirmPayload } from '@/components/project/ServicePickerDialog.vue'
import Stepper from '@/components/common/Stepper.vue'
import TextInput from '@/components/common/TextInput.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useFormValidation } from '@/composables/useFormValidation'
import { usePermitCatalogStore } from '@/stores/permitCatalogStore'
import { useProjectStore } from '@/stores/projectStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import { useServiceCatalogStore } from '@/stores/serviceCatalogStore'
import { useToastStore } from '@/stores/toastStore'
import { useUserStore } from '@/stores/userStore'
import type { Project, ProjectPriority, SelectedSupervisionActivity } from '@/types/Project'
import type { PermitCatalogItem } from '@/types/PermitCatalog'
import type { SelectedServiceActivity } from '@/types/ServiceCatalog'
import type { SelectOption } from '@/types/Ui'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { validators } from '@/utils/validators'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()
const resultDialogStore = useResultDialogStore()
const toastStore = useToastStore()
const userStore = useUserStore()
const serviceCatalogStore = useServiceCatalogStore()
const permitCatalogStore = usePermitCatalogStore()
const { t } = useI18n()

const WIZARD_STEPS = computed(() => [
  { label: t('project.newWizard.steps.clientService') },
  { label: t('project.newWizard.steps.projectDetails') },
  { label: t('project.newWizard.steps.reviewConfirm') },
])

const PRIORITY_OPTIONS = computed<SelectOption[]>(() => [
  { label: t('project.priority.high'), value: 'High' },
  { label: t('project.priority.medium'), value: 'Medium' },
  { label: t('project.priority.low'), value: 'Low' },
])

const currentStep = ref(0)
const isSubmitting = ref(false)
const showConfirmation = ref(false)
const createdProject = ref<Project | null>(null)
const isServicePickerOpen = ref(false)

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
  siteAddress: '',
  startDate: '',
  targetDate: '',
  // Supervision picks from the same unified ServicePickerDialog -- each
  // activity carries its own start/end window, and supervisionStartDate/
  // supervisionEndDate is the overall engagement window (required once
  // any activity is selected, enforced both in the picker and server-side).
  selectedSupervisionActivities: [] as SelectedSupervisionActivity[],
  supervisionStartDate: '' as string | null,
  supervisionEndDate: '' as string | null,
  // Permits this project needs to apply for, picked in the same unified
  // ServicePickerDialog as Design services and Supervision -- optional,
  // distinct from the client-already-holds permits step this wizard
  // doesn't have.
  selectedPermits: [] as PermitCatalogItem[],
})

const supervisionMonthlyTotal = computed(() =>
  form.selectedSupervisionActivities.reduce((sum, item) => sum + item.monthlyRate, 0),
)

// Scope of Work is a plain preview, derived entirely from whatever was
// picked in the unified service picker -- "scope = services +
// supervision + permits", per the actual requirement -- and shown
// read-only on the Review step, not a field staff type into
// themselves (there's nothing else for it to diverge from, so this is
// a plain computed rather than a watch-and-sync-unless-edited field).
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
  if (form.selectedSupervisionActivities.length > 0) {
    if (lines.length > 0) lines.push('')
    lines.push('Supervision Activities:')
    // No price here -- same "name only" convention as the Design
    // services above; this text is a description, not a quote (the
    // Service picker's own button/summary already shows pricing).
    form.selectedSupervisionActivities.forEach((item) => lines.push(`- ${item.activityName}`))
  }
  if (form.selectedPermits.length > 0) {
    if (lines.length > 0) lines.push('')
    lines.push('Permits to Apply For:')
    form.selectedPermits.forEach((permit) => lines.push(`- ${permit.name}`))
  }
  return lines.join('\n')
}

const scopeText = computed(buildScopeText)

const serviceTotal = computed(() => form.selectedActivities.reduce((sum, item) => sum + item.fixedCost, 0))

const { errors, setRules, validateAll } = useFormValidation()

setRules({
  clientId: [validators.required('Please select a client')],
  selectedActivities: [
    () =>
      form.selectedActivities.length > 0 || form.selectedSupervisionActivities.length > 0
        ? true
        : 'Please select at least one service or Supervision activity',
  ],
  engineer: [validators.required('Please assign an engineer')],
  projectName: [validators.required('Project name is required'), validators.minLength(5)],
  startDate: [validators.required('Start date is required')],
  targetDate: [validators.required('Target date is required')],
})

function handleServicesConfirmed(payload: ServicePickerConfirmPayload): void {
  form.selectedActivities = payload.design
  form.selectedSupervisionActivities = payload.supervision
  form.supervisionStartDate = payload.supervisionStartDate
  form.supervisionEndDate = payload.supervisionEndDate
  form.selectedPermits = payload.permits
  const names = new Set(payload.design.map((item) => item.serviceName))
  if (payload.supervision.length > 0) names.add('Supervision')
  form.service = [...names].join(', ')
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
  // catalog (Administration > Catalogs > Service Catalog) and feed the service picker
  // dialog directly, so anything added there shows up here without a code
  // change. Fetched fresh for the same reason as the client list above.
  await serviceCatalogStore.loadServices()
  if (permitCatalogStore.permits.length === 0) await permitCatalogStore.loadPermits()
  // Only Active clients can have a project created for them -- a project
  // needs a real, currently active client relationship behind it, not
  // one the business has since deactivated.
  const activeClients = projectStore.clients.filter((client) => client.status === 'Active')
  hasIneligibleClients.value = activeClients.length < projectStore.clients.length
  clientOptions.value = activeClients.map((client) => ({ label: client.companyName, value: client.id }))

  // Arriving from a client's own workspace page ("New Project" there)
  // pre-selects that client -- saves a step and rules out picking the
  // wrong one out of a long list. Only pre-fills if the client is
  // actually eligible (Active); if not, the wizard's own "No eligible
  // clients" / ineligible-clients messaging below still explains why,
  // rather than silently pre-selecting something invalid.
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

  // This store swallows a failed load into its own `.error` field rather
  // than throwing (see serviceCatalogStore), which otherwise looks
  // identical to "the catalog is genuinely empty" -- the service picker
  // has no error state of its own and would just print "No Design
  // services in the catalog yet." either way. Surface it here instead so
  // a real load failure (permissions, network) is never silently
  // indistinguishable from an empty catalog.
  if (serviceCatalogStore.error) {
    toastStore.show('error', t('project.newWizard.couldNotLoadServiceCatalog'), serviceCatalogStore.error)
  }
})

const STEP_FIELDS: Record<number, (keyof typeof form)[]> = {
  0: ['clientId', 'selectedActivities', 'engineer'],
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
  if (!validateStep(currentStep.value)) {
    // Previously a silent no-op: the button just did nothing, with the
    // only sign anything was wrong being red text under a field that
    // might be scrolled out of view -- easy to read as "this isn't
    // working" rather than "something needs fixing here."
    toastStore.show(
      'error',
      t('project.newWizard.pleaseFixHighlightedFields'),
      t('project.newWizard.fieldsNeedAttentionUnderStep', { step: WIZARD_STEPS.value[currentStep.value].label }),
    )
    return
  }
  currentStep.value = Math.min(currentStep.value + 1, WIZARD_STEPS.value.length - 1)
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
  // duplicate projects and a confirmation dialog that ended up
  // reflecting whichever call finished last rather than clearly
  // confirming the one thing that was asked for.
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
      t('project.newWizard.pleaseFixHighlightedFields'),
      t('project.newWizard.earlierFieldsNeedAttention'),
    )
    currentStep.value = 0
    return
  }

  isSubmitting.value = true

  try {
    const project = await projectStore.createProject({
      projectName: form.projectName,
      description: scopeText.value || undefined,
      siteAddress: form.siteAddress || undefined,
      clientId: form.clientId,
      service: form.service,
      selectedActivities: form.selectedActivities,
      serviceTotal: serviceTotal.value,
      engineerId: form.engineer,
      priority: form.priority,
      startDate: form.startDate,
      targetDate: form.targetDate,
      // Optional -- only sent when something was actually checked, so an
      // unaware/older backend (or simply a project that skipped
      // Supervision entirely) doesn't get an empty/meaningless selection.
      selectedSupervisionActivities:
        form.selectedSupervisionActivities.length > 0 ? form.selectedSupervisionActivities : undefined,
      supervisionStartDate: form.supervisionStartDate || undefined,
      supervisionEndDate: form.supervisionEndDate || undefined,
      selectedPermits:
        form.selectedPermits.length > 0
          ? form.selectedPermits.map((permit) => ({ permitId: permit.id, permitName: permit.name }))
          : undefined,
    })

    createdProject.value = project
    showConfirmation.value = true
  } catch (error) {
    // An explicit, must-acknowledge dialog rather than a toast -- same
    // reasoning as every other create-style wizard in the app (see
    // NewClientWizardPage.vue): a toast auto-dismisses in 4 seconds, so
    // a failure here could come and go while attention was on the form
    // (or the confirmation that never appeared), reading as "nothing
    // happened" rather than "this needs a fix."
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseCheckFormAndTryAgain')
    resultDialogStore.showError(t('project.newWizard.failedToCreateProject'), detail)
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
    <PageHeader :title="t('project.newWizard.title')" :subtitle="t('project.newWizard.subtitle')" />

    <div class="rounded-xl border border-border-light bg-bg-card p-6">
      <Stepper :steps="WIZARD_STEPS" :current-step="currentStep" />

      <div class="mt-8">
        <FormSection
          v-if="currentStep === 0"
          :title="t('project.newWizard.clientServiceTitle')"
          :description="t('project.newWizard.clientServiceDescription')"
        >
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <div class="flex flex-col gap-1.5">
              <SelectBox
                v-model="form.clientId"
                :label="t('project.newWizard.client')"
                :placeholder="t('project.newWizard.selectClient')"
                required
                :options="clientOptions"
                :error="errors.clientId"
              />
              <p v-if="clientOptions.length === 0" class="text-xs text-warning-600">
                {{ t('project.newWizard.noEligibleClients') }}
              </p>
              <p v-else-if="hasIneligibleClients" class="text-xs text-text-muted">
                {{ t('project.newWizard.onlyEligibleClientsShown') }}
              </p>
              <RouterLink :to="{ name: ROUTE_NAMES.CLIENT_NEW }" class="self-start text-xs font-medium text-primary-600 hover:text-primary-700">
                {{ t('project.newWizard.onboardNewClient') }}
              </RouterLink>
            </div>
            <div class="flex flex-col gap-1.5">
              <label id="service-picker-label" class="text-sm font-medium text-text-secondary">{{ t('project.newWizard.service') }} <span class="text-danger-500">*</span></label>
              <button
                id="service-picker-button"
                type="button"
                aria-labelledby="service-picker-label service-picker-button"
                class="flex min-h-[42px] w-full items-center justify-between rounded-lg border bg-bg-card px-3 py-2 text-start text-sm transition-colors duration-fast hover:bg-bg-hover"
                :class="errors.selectedActivities ? 'border-danger-500' : 'border-border-default'"
                @click="isServicePickerOpen = true"
              >
                <span
                  v-if="form.selectedActivities.length === 0 && form.selectedSupervisionActivities.length === 0 && form.selectedPermits.length === 0"
                  class="text-text-muted"
                >
                  {{ t('project.newWizard.selectService') }}
                </span>
                <span v-else class="text-text-primary">
                  <template v-if="form.selectedActivities.length > 0">
                    {{ t('project.newWizard.activityCount', form.selectedActivities.length) }} ·
                    {{ formatCurrency(serviceTotal, 'KWD') }}
                  </template>
                  <template v-if="form.selectedActivities.length > 0 && form.selectedSupervisionActivities.length > 0"> + </template>
                  <template v-if="form.selectedSupervisionActivities.length > 0">
                    {{ t('project.newWizard.supervisionCount', form.selectedSupervisionActivities.length) }} ·
                    {{ formatCurrency(supervisionMonthlyTotal, 'KWD') }}/mo
                  </template>
                  <template v-if="(form.selectedActivities.length > 0 || form.selectedSupervisionActivities.length > 0) && form.selectedPermits.length > 0"> + </template>
                  <template v-if="form.selectedPermits.length > 0">
                    {{ t('project.newWizard.permitCount', form.selectedPermits.length) }}
                  </template>
                </span>
                <span class="text-xs font-medium text-primary-600">
                  {{
                    form.selectedActivities.length === 0 && form.selectedSupervisionActivities.length === 0 && form.selectedPermits.length === 0
                      ? t('project.newWizard.choose')
                      : t('project.newWizard.edit')
                  }}
                </span>
              </button>
              <p v-if="errors.selectedActivities" class="text-xs text-danger-600">{{ errors.selectedActivities }}</p>
              <p v-else-if="form.service" class="truncate text-xs text-text-muted">{{ form.service }}</p>
              <p v-if="form.selectedPermits.length > 0" class="truncate text-xs text-text-muted">
                {{ t('project.overviewTab.permitsTitle') }}: {{ form.selectedPermits.map((p) => p.name).join(', ') }}
              </p>
            </div>
            <SelectBox
              v-model="form.engineer"
              :label="t('project.newWizard.fieldEngineer')"
              :placeholder="t('project.newWizard.assignEngineer')"
              required
              :options="engineerOptions"
              :error="errors.engineer"
            />
            <RadioGroup v-model="form.priority" :label="t('project.newWizard.priority')" :options="PRIORITY_OPTIONS" :vertical="false" />
          </div>
        </FormSection>

        <FormSection
          v-else-if="currentStep === 1"
          :title="t('project.newWizard.projectDetailsTitle')"
          :description="t('project.newWizard.projectDetailsDescription')"
        >
          <TextInput
            v-model="form.projectName"
            :label="t('project.newWizard.projectName')"
            placeholder="e.g. Al Reem Residential Tower - Structural Design"
            required
            :error="errors.projectName"
          />
          <TextInput
            v-model="form.siteAddress"
            :label="t('project.newWizard.siteAddress')"
            placeholder="e.g. Plot 572, Parcel 4, Second Suburb, Al Mutlaa"
            :hint="t('project.newWizard.siteAddressHint')"
          />
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <DatePicker v-model="form.startDate" :label="t('project.newWizard.startDate')" required :error="errors.startDate" />
            <DatePicker v-model="form.targetDate" :label="t('project.newWizard.targetDate')" required :error="errors.targetDate" />
          </div>
        </FormSection>

        <FormSection v-else :title="t('project.newWizard.reviewTitle')" :description="t('project.newWizard.reviewDescription')">
          <div class="grid grid-cols-1 gap-x-8 gap-y-4 tablet:grid-cols-2">
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.newWizard.client') }}</p>
              <p class="text-sm text-text-primary">{{ selectedClientName() }}</p>
            </div>
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.newWizard.projectName') }}</p>
              <p class="text-sm text-text-primary">{{ form.projectName || t('project.newWizard.notEntered') }}</p>
            </div>
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.newWizard.startDate') }}</p>
              <p class="text-sm text-text-primary">{{ form.startDate ? formatDate(form.startDate) : t('project.newWizard.notSet') }}</p>
            </div>
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.newWizard.targetDate') }}</p>
              <p class="text-sm text-text-primary">{{ form.targetDate ? formatDate(form.targetDate) : t('project.newWizard.notSet') }}</p>
            </div>
            <div class="tablet:col-span-2">
              <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.newWizard.scopeOfWork') }}</p>
              <p class="whitespace-pre-line text-sm text-text-primary">{{ scopeText || t('project.newWizard.notEntered') }}</p>
            </div>
            <div>
              <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.newWizard.fieldEngineer') }}</p>
              <p class="text-sm text-text-primary">{{ selectedEngineerName() }}</p>
            </div>
          </div>
        </FormSection>
      </div>

      <div class="mt-8 flex flex-col gap-2 border-t border-border-light pt-4">
        <div class="flex items-center justify-between">
          <FormActionBar
            v-if="currentStep === 0"
            :cancel-label="t('project.newWizard.cancel')"
            :submit-label="t('project.newWizard.next')"
            @cancel="cancelWizard"
            @submit="goNext"
          />
          <FormActionBar
            v-else-if="currentStep < WIZARD_STEPS.length - 1"
            :cancel-label="t('project.newWizard.back')"
            :submit-label="t('project.newWizard.next')"
            @cancel="goBack"
            @submit="goNext"
          />
          <FormActionBar
            v-else
            :cancel-label="t('project.newWizard.back')"
            :submit-label="t('project.newWizard.createProject')"
            :loading="isSubmitting"
            @cancel="goBack"
            @submit="submitWizard"
          />
        </div>
        <!-- Creating the project also sends the client an informational
             "project created" email in the same request -- a bare
             spinner with no explanation read as stuck during that wait. -->
        <p v-if="isSubmitting" class="text-end text-xs text-text-muted">
          {{ t('project.newWizard.submittingNotice') }}
        </p>
      </div>
    </div>

    <ServicePickerDialog
      v-model="isServicePickerOpen"
      :services="serviceCatalogStore.services"
      :selected-design="form.selectedActivities"
      :selected-supervision="form.selectedSupervisionActivities"
      :supervision-start-date="form.supervisionStartDate"
      :supervision-end-date="form.supervisionEndDate"
      show-permits
      :permits="permitCatalogStore.permits"
      :selected-permits="form.selectedPermits"
      currency="KWD"
      @confirm="handleServicesConfirmed"
    />

    <BaseDialog :model-value="showConfirmation" :title="t('project.newWizard.projectCreatedTitle')" size="sm" :closable="false">
      <p class="text-sm text-text-secondary">
        <strong>{{ createdProject?.projectName }}</strong>
        {{ t('project.newWizard.projectCreatedMessagePart1') }}
        <strong>{{ createdProject?.projectNo }}</strong>
        {{ t('project.newWizard.projectCreatedMessagePart2') }} <strong>{{ selectedClientName() }}</strong>.
      </p>

      <template #footer>
        <BaseButton variant="primary" @click="goToCreatedProject">{{ t('project.newWizard.viewProjectWorkspace') }}</BaseButton>
      </template>
    </BaseDialog>
  </div>
</template>
