<script setup lang="ts">
import { Plus, Trash2 } from '@lucide/vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import Divider from '@/components/common/Divider.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TextInput from '@/components/common/TextInput.vue'
import WorkflowProgress from '@/components/project/WorkflowProgress.vue'
import { useFormValidation } from '@/composables/useFormValidation'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type { QuotationLineItemInput } from '@/services/quotationService'
import type { Project, ProjectWorkspaceTabKey } from '@/types/Project'
import { getClientDisplayName } from '@/utils/clientHelpers'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate, todayIso } from '@/utils/dateFormatter'
import { validators } from '@/utils/validators'

// Dedicated route for creating a quotation. Editing an existing
// quotation happens inline on the Quotation tab (QuotationPreview.vue).

// Quotations always price in the company's one operating currency.
const QUOTATION_CURRENCY = 'KWD'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const projectStore = useProjectStore()
const quotationStore = useQuotationStore()
const resultDialogStore = useResultDialogStore()

const projectId = computed(() => route.params.projectId as string)

const isLoading = ref(true)

async function loadData(): Promise<void> {
  isLoading.value = true
  if (projectStore.projects.length === 0) await projectStore.loadProjects()
  await quotationStore.loadQuotationsForProject(projectId.value)
  isLoading.value = false
}
onMounted(loadData)
watch(projectId, loadData)

const project = computed(() => projectStore.getProjectById(projectId.value))
const client = computed(() => (project.value ? projectStore.getClientById(project.value.clientId) : undefined))

// A Draft or Approved quotation blocks creating a new one for this project.
const hasActiveQuotation = computed(() =>
  quotationStore.quotations.some((quotation) => quotation.status === 'Draft' || quotation.status === 'Approved'),
)

function goBack(): void {
  if (project.value) {
    router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId: project.value.id }, query: { tab: 'quotation' } })
    return
  }
  router.push({ name: ROUTE_NAMES.PROJECTS })
}

// Lets staff jump to any stage of the project, not just back to Quotation.
function navigateToTab(tab: ProjectWorkspaceTabKey): void {
  if (!project.value) return
  router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId: project.value.id }, query: { tab } })
}

interface DraftLineItem {
  description: string
  quantity: number
  unitPrice: number
  // True for a row seeded from the project's picked Design activities
  // or Permits: its description and rate render as fixed text since
  // they reflect the agreed scope. A row added via Add Service is
  // free-text/free-rate instead.
  fromScope: boolean
}

function emptyLineItem(): DraftLineItem {
  return { description: '', quantity: 1, unitPrice: 0, fromScope: false }
}

function emptyForm() {
  return {
    validity: '',
    discountAmount: 0,
    lineItems: [emptyLineItem()] as DraftLineItem[],
  }
}

// Turns the project's picked Design activities and Permits into priced
// draft line items (one per item, quantity 1, unit price = the picked
// fixedCost/permitPrice). Falls back to emptyForm()'s single blank row
// when the project has no picks yet.
//
// Supervision activities are excluded: Supervision is billed monthly
// via the Financial Agreement, not as a one-time fee, so it's shown
// separately as a non-priced reference instead (see
// supervisionActivities/the template).
function formFromProject(project: Project | undefined) {
  const serviceLineItems = (project?.selectedActivities ?? []).map((item) => ({
    description: `${item.serviceName} - ${item.activityName}`,
    quantity: 1,
    unitPrice: item.fixedCost,
    fromScope: true,
  }))
  const permitLineItems = (project?.selectedPermits ?? []).map((permit) => ({
    description: `Permits to Apply For - ${permit.permitName}`,
    quantity: 1,
    unitPrice: permit.permitPrice ?? 0,
    fromScope: true,
  }))
  const lineItems = [...serviceLineItems, ...permitLineItems]
  if (lineItems.length === 0) return emptyForm()
  return { ...emptyForm(), lineItems }
}

// Reference-only -- see formFromProject's comment above for why these
// never join form.lineItems/subtotal/total.
const supervisionActivities = computed(() => project.value?.selectedSupervisionActivities ?? [])

const form = reactive(emptyForm())
interface LineItemError {
  description?: string
  quantity?: string
  unitPrice?: string
}
const lineItemErrors = reactive<LineItemError[]>([])
const { errors, setRules, validateAll } = useFormValidation()

setRules({
  validity: [validators.required('Validity date is required'), validators.notPastDate('Validity date cannot be in the past')],
  discountAmount: [
    () => form.discountAmount <= subtotal.value || t('project.newQuotationDialog.discountExceedsSubtotal'),
  ],
})

// Seeds once the project has finished loading, rather than on every
// reactive change to it -- re-seeding after the user has started
// editing would silently discard their in-progress edits.
const isFormSeeded = ref(false)
watch(
  () => [isLoading.value, project.value] as const,
  ([loading, proj]) => {
    if (loading || isFormSeeded.value) return
    Object.assign(form, formFromProject(proj))
    isFormSeeded.value = true
    revalidate()
  },
  { immediate: true },
)

function addLineItem(): void {
  form.lineItems.push(emptyLineItem())
}

function removeLineItem(index: number): void {
  if (form.lineItems.length === 1) return // always keep at least one row
  form.lineItems.splice(index, 1)
}

// Mirrors utils/quotationHelpers.ts's calculateQuotationPricing() exactly.
const subtotal = computed(() => form.lineItems.reduce((sum, item) => sum + item.quantity * item.unitPrice, 0))
const total = computed(() => subtotal.value - form.discountAmount)

function revalidate(): void {
  validateAll(form)
}
watch(form, revalidate, { deep: true })

const isSubmitting = ref(false)

async function handleSubmit(): Promise<void> {
  const formValid = validateAll(form)

  const itemErrors: LineItemError[] = form.lineItems.map((item) => {
    const rowError: LineItemError = {}
    if (!item.description.trim()) rowError.description = t('project.newQuotationDialog.descriptionRequired')
    if (item.quantity <= 0) rowError.quantity = t('project.newQuotationDialog.quantityMustBePositive')
    if (item.unitPrice < 0) rowError.unitPrice = t('project.newQuotationDialog.unitPriceCannotBeNegative')
    return rowError
  })
  lineItemErrors.splice(0, lineItemErrors.length, ...itemErrors)
  const lineItemsValid = itemErrors.every((rowError) => Object.keys(rowError).length === 0)

  if (!formValid || !lineItemsValid) return

  const lineItems: QuotationLineItemInput[] = form.lineItems.map((item) => ({
    description: item.description.trim(),
    quantity: item.quantity,
    unitPrice: item.unitPrice,
  }))

  isSubmitting.value = true
  try {
    const quotation = await quotationStore.createQuotation({
      projectId: projectId.value,
      validity: form.validity,
      currency: QUOTATION_CURRENCY,
      discountAmount: form.discountAmount,
      lineItems,
    })
    // Creating a quotation can move current_stage server-side (see
    // quotation_service.create_quotation -> try_auto_advance_stage) --
    // refresh the shared project store's cached copy.
    await projectStore.refreshProject(projectId.value)
    resultDialogStore.showSuccess(t('project.quotationTab.quotationCreatedTitle'), t('common.createdSuccessfully', { no: quotation.quotationNo }))
    goBack()
  } catch (error) {
    resultDialogStore.showError(t('project.quotationTab.failedToCreateQuotation'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <WorkflowProgress
      v-if="project"
      class="no-print"
      :current-stage="project.currentStage"
      :project-status="project.status"
      :includes-design="project.includesDesign"
      :includes-government-submission="project.includesGovernmentSubmission"
      :includes-supervision="project.includesSupervision"
      :selected-activities="project.selectedActivities"
      :selected-permits="project.selectedPermits"
      :selected-supervision-activities="project.selectedSupervisionActivities"
      @navigate-tab="navigateToTab"
    />

    <div v-if="isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="8" />
    </div>

    <EmptyState v-else-if="!project" :title="t('project.workspacePage.notFoundTitle')" :description="t('project.workspacePage.notFoundDescription')" />

    <EmptyState
      v-else-if="hasActiveQuotation"
      :title="t('project.quotationTab.quotationAlreadyApprovedTitle')"
      :description="t('project.quotationTab.quotationAlreadyApprovedDescription')"
    />

    <div v-else class="rounded-xl border border-border-light bg-bg-card p-5">
      <h1 class="mb-4 text-lg font-semibold text-text-primary">{{ t('project.newQuotationDialog.title') }}</h1>

      <div class="flex flex-col gap-5">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <TextInput :model-value="client ? getClientDisplayName(client) : ''" :label="t('project.newQuotationDialog.client')" disabled />
          <TextInput :model-value="`${project.projectName} (${project.projectNo})`" :label="t('project.newQuotationDialog.project')" disabled />
        </div>

        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <TextInput :model-value="formatDate(todayIso())" :label="t('project.newQuotationDialog.quotationDate')" disabled />
          <DatePicker v-model="form.validity" :label="t('project.newQuotationDialog.validUntil')" required :min="todayIso()" :error="errors.validity" />
        </div>

        <div class="flex flex-col gap-3">
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium text-text-secondary">{{ t('project.newQuotationDialog.lineItems') }}</label>
            <BaseButton variant="ghost" size="sm" :icon="Plus" @click="addLineItem">{{ t('project.newQuotationDialog.addLineItem') }}</BaseButton>
          </div>

          <div class="overflow-x-auto rounded-lg border border-border-light">
            <table class="w-full min-w-[640px] border-collapse">
              <thead>
                <tr class="border-b border-border-light bg-bg-secondary">
                  <th class="w-12 px-3 py-2.5 text-start text-xs font-semibold uppercase tracking-wide text-text-muted">
                    {{ t('project.newQuotationDialog.columnSerialNo') }}
                  </th>
                  <th class="px-3 py-2.5 text-start text-xs font-semibold uppercase tracking-wide text-text-muted">
                    {{ t('project.newQuotationDialog.columnLineItem') }}
                  </th>
                  <th class="w-24 px-3 py-2.5 text-end text-xs font-semibold uppercase tracking-wide text-text-muted">
                    {{ t('project.newQuotationDialog.columnQty') }}
                  </th>
                  <th class="w-36 px-3 py-2.5 text-end text-xs font-semibold uppercase tracking-wide text-text-muted">
                    {{ t('project.newQuotationDialog.columnRate') }}
                  </th>
                  <th class="w-36 px-3 py-2.5 text-end text-xs font-semibold uppercase tracking-wide text-text-muted">
                    {{ t('project.newQuotationDialog.columnAmount') }}
                  </th>
                  <th class="w-10 px-2 py-2.5"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in form.lineItems" :key="index" class="border-b border-border-light last:border-0">
                  <td class="px-3 py-2 align-top">
                    <span class="inline-block pt-2 text-sm text-text-secondary">{{ index + 1 }}</span>
                  </td>
                  <td class="px-3 py-2 align-top">
                    <TextInput
                      v-if="!item.fromScope"
                      v-model="item.description"
                      :placeholder="t('project.newQuotationDialog.descriptionPlaceholder')"
                      :error="lineItemErrors[index]?.description"
                    />
                    <span v-else class="inline-block pt-2 text-sm text-text-secondary">{{ item.description }}</span>
                  </td>
                  <td class="px-3 py-2 align-top">
                    <NumberInput
                      :model-value="item.quantity"
                      :min="0.01"
                      step="0.01"
                      :error="lineItemErrors[index]?.quantity"
                      @update:model-value="item.quantity = Number($event)"
                    />
                  </td>
                  <td class="px-3 py-2 align-top">
                    <NumberInput
                      v-if="!item.fromScope"
                      :model-value="item.unitPrice"
                      :prefix="QUOTATION_CURRENCY"
                      :min="0"
                      step="0.01"
                      :error="lineItemErrors[index]?.unitPrice"
                      @update:model-value="item.unitPrice = Number($event)"
                    />
                    <span v-else class="inline-block pt-2 text-end text-sm text-text-secondary">{{ formatCurrency(item.unitPrice, QUOTATION_CURRENCY) }}</span>
                  </td>
                  <td class="px-3 py-2 text-end align-top">
                    <span class="inline-block pt-2 text-sm font-medium text-text-primary">
                      {{ formatCurrency(item.quantity * item.unitPrice, QUOTATION_CURRENCY) }}
                    </span>
                  </td>
                  <td class="px-2 py-2 text-end align-top">
                    <IconButton
                      :icon="Trash2"
                      :label="t('project.newQuotationDialog.removeLineItem', { number: index + 1 })"
                      size="sm"
                      :disabled="form.lineItems.length === 1"
                      @click="removeLineItem(index)"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <NumberInput
            :model-value="form.discountAmount"
            :label="t('project.newQuotationDialog.discountAmount')"
            :prefix="QUOTATION_CURRENCY"
            :min="0"
            step="1"
            :error="errors.discountAmount"
            @update:model-value="form.discountAmount = Number($event)"
          />
        </div>

        <Divider />

        <div class="flex flex-col gap-2 text-sm">
          <div class="flex items-center justify-between text-text-secondary">
            <span>{{ t('project.newQuotationDialog.subtotal') }}</span>
            <span class="font-medium text-text-primary">{{ formatCurrency(subtotal, QUOTATION_CURRENCY) }}</span>
          </div>
          <div v-if="form.discountAmount > 0" class="flex items-center justify-between text-text-secondary">
            <span>{{ t('project.newQuotationDialog.discount') }}</span>
            <span class="font-medium text-danger-700">-{{ formatCurrency(form.discountAmount, QUOTATION_CURRENCY) }}</span>
          </div>
          <Divider />
          <div class="flex items-center justify-between">
            <span class="text-sm font-semibold text-text-primary">{{ t('project.newQuotationDialog.total') }}</span>
            <span class="text-lg font-semibold text-primary-700">{{ formatCurrency(total, QUOTATION_CURRENCY) }}</span>
          </div>
        </div>

        <div v-if="supervisionActivities.length > 0" class="flex flex-col gap-2 rounded-lg border border-border-light bg-bg-secondary p-3">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.newQuotationDialog.supervisionReferenceTitle') }}</p>
          <p class="text-xs text-text-muted">{{ t('project.newQuotationDialog.supervisionReferenceHint') }}</p>
          <div v-for="activity in supervisionActivities" :key="activity.activityId" class="flex items-center justify-between text-sm">
            <span class="text-text-secondary">{{ activity.activityName }} ({{ formatDate(activity.startDate) }} – {{ formatDate(activity.endDate) }})</span>
            <span class="font-medium text-text-primary">{{ formatCurrency(activity.monthlyRate, QUOTATION_CURRENCY) }}/mo</span>
          </div>
        </div>
      </div>

      <div class="mt-6 flex justify-end gap-3">
        <BaseButton variant="secondary" :disabled="isSubmitting" @click="goBack">{{ t('common.cancel') }}</BaseButton>
        <BaseButton :loading="isSubmitting" @click="handleSubmit">{{ t('project.newQuotationDialog.createQuotation') }}</BaseButton>
      </div>
    </div>
  </div>
</template>
