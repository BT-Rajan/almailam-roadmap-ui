<script setup lang="ts">
import { ArrowLeft, ArrowRight, Plus, Trash2 } from '@lucide/vue'
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
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useFormValidation } from '@/composables/useFormValidation'
import { useLocale } from '@/composables/useLocale'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useToastStore } from '@/stores/toastStore'
import type { QuotationLineItemInput } from '@/services/quotationService'
import type { Project } from '@/types/Project'
import { getClientDisplayName } from '@/utils/clientHelpers'
import { formatCurrency } from '@/utils/currencyFormatter'
import { todayIso } from '@/utils/dateFormatter'
import { validators } from '@/utils/validators'

// Replaces NewQuotationDialog.vue's modal -- a dedicated route
// (/projects/:projectId/quotation/new), same treatment as
// TaskCreatePage.vue/PaymentPlanFormPage.vue. Create only -- editing an
// existing quotation stays inline on the Quotation tab
// (QuotationPreview.vue's own @patch).

// The quotation always prices in the company's one operating currency --
// there was never actually a need for staff to pick a different one per
// quotation.
const QUOTATION_CURRENCY = 'KWD'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isRtl } = useLocale()
const projectStore = useProjectStore()
const quotationStore = useQuotationStore()
const toastStore = useToastStore()

const backIcon = computed(() => (isRtl.value ? ArrowRight : ArrowLeft))
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

// Once one quotation for this project has been Approved, that's the
// quotation the project moves forward on -- creating another would just
// be a second, competing quotation for the same project (matches
// ProjectQuotationTab.vue's own hasApprovedQuotation).
const hasApprovedQuotation = computed(() => quotationStore.quotations.some((quotation) => quotation.status === 'Approved'))

function goBack(): void {
  if (project.value) {
    router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId: project.value.id }, query: { tab: 'quotation' } })
    return
  }
  router.push({ name: ROUTE_NAMES.PROJECTS })
}

interface DraftLineItem {
  description: string
  quantity: number
  unitPrice: number
}

function emptyLineItem(): DraftLineItem {
  return { description: '', quantity: 1, unitPrice: 0 }
}

function emptyForm() {
  return {
    validity: '',
    discountAmount: 0,
    notes: '',
    termsText: '',
    scopePhasesText: '',
    paymentTermsText: '',
    lineItems: [emptyLineItem()] as DraftLineItem[],
  }
}

// Turns the project's picked activities into draft line items (one per
// activity, quantity 1, unit price = the picked fixedCost). Falls back to
// emptyForm()'s single blank row when the project has no picks yet.
//
// Also appends one line per selected Supervision activity (informational
// only -- Supervision is actually billed through the Financial
// Agreement's prorated monthly schedule once the project reaches
// Contract) and one per selected Permit.
function formFromProject(project: Project | undefined) {
  const serviceLineItems = (project?.selectedActivities ?? []).map((item) => ({
    description: `${item.serviceName} - ${item.activityName}`,
    quantity: 1,
    unitPrice: item.fixedCost,
  }))
  const supervisionLineItems = (project?.selectedSupervisionActivities ?? []).map((activity) => ({
    description: `Supervision - ${activity.activityName} (Monthly, ${activity.startDate} to ${activity.endDate})`,
    quantity: 1,
    unitPrice: activity.monthlyRate,
  }))
  const permitLineItems = (project?.selectedPermits ?? []).map((permit) => ({
    description: `Permits to Apply For - ${permit.permitName}`,
    quantity: 1,
    unitPrice: permit.permitPrice ?? 0,
  }))
  const lineItems = [...serviceLineItems, ...supervisionLineItems, ...permitLineItems]
  if (lineItems.length === 0) return emptyForm()
  return { ...emptyForm(), lineItems, scopePhasesText: buildScopeText(project) }
}

// Mirrors NewProjectWizardPage.vue's buildScopeText exactly, grouped the
// same way (Architectural Design / Supervision Activities / Permits to
// Apply For).
function buildScopeText(project: Project | undefined): string {
  const lines: string[] = []
  const activitiesByService = new Map<string, string[]>()
  for (const item of project?.selectedActivities ?? []) {
    const list = activitiesByService.get(item.serviceName) ?? []
    list.push(item.activityId === item.serviceId ? item.serviceName : item.activityName)
    activitiesByService.set(item.serviceName, list)
  }
  for (const [serviceName, activityNames] of activitiesByService) {
    lines.push(`${serviceName}:`)
    activityNames.forEach((name) => lines.push(`- ${name}`))
  }
  const supervisionActivities = project?.selectedSupervisionActivities ?? []
  if (supervisionActivities.length > 0) {
    if (lines.length > 0) lines.push('')
    lines.push('Supervision Activities:')
    supervisionActivities.forEach((item) => lines.push(`- ${item.activityName}`))
  }
  const permits = project?.selectedPermits ?? []
  if (permits.length > 0) {
    if (lines.length > 0) lines.push('')
    lines.push('Permits to Apply For:')
    permits.forEach((permit) => lines.push(`- ${permit.permitName}`))
  }
  return lines.join('\n')
}

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
      notes: form.notes.trim() || undefined,
      termsAndConditions: form.termsText
        .split('\n')
        .map((line) => line.trim())
        .filter((line) => line.length > 0),
      scopePhases: form.scopePhasesText
        .split('\n')
        .map((line) => line.trim())
        .filter((line) => line.length > 0),
      paymentTerms: form.paymentTermsText
        .split('\n')
        .map((line) => line.trim())
        .filter((line) => line.length > 0),
      lineItems,
    })
    // Creating a quotation can move current_stage server-side (see
    // quotation_service.create_quotation -> try_auto_advance_stage) --
    // refresh the shared project store's cached copy.
    await projectStore.refreshProject(projectId.value)
    toastStore.show('success', t('project.quotationTab.quotationCreatedTitle'), t('common.createdSuccessfully', { no: quotation.quotationNo }))
    goBack()
  } catch (error) {
    toastStore.show('error', t('project.quotationTab.failedToCreateQuotation'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <BaseButton variant="ghost" size="sm" :icon="backIcon" class="self-start no-print" @click="goBack">
      {{ t('project.newQuotationDialog.backToQuotation') }}
    </BaseButton>

    <div v-if="isLoading" class="max-w-3xl rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="8" />
    </div>

    <EmptyState v-else-if="!project" :title="t('project.workspacePage.notFoundTitle')" :description="t('project.workspacePage.notFoundDescription')" />

    <EmptyState
      v-else-if="hasApprovedQuotation"
      :title="t('project.quotationTab.quotationAlreadyApprovedTitle')"
      :description="t('project.quotationTab.quotationAlreadyApprovedDescription')"
    />

    <div v-else class="max-w-3xl rounded-xl border border-border-light bg-bg-card p-5">
      <h1 class="mb-4 text-lg font-semibold text-text-primary">{{ t('project.newQuotationDialog.title') }}</h1>

      <div class="flex flex-col gap-5">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <TextInput :model-value="client ? getClientDisplayName(client) : ''" :label="t('project.newQuotationDialog.client')" disabled />
          <TextInput :model-value="`${project.projectName} (${project.projectNo})`" :label="t('project.newQuotationDialog.project')" disabled />
        </div>

        <DatePicker v-model="form.validity" :label="t('project.newQuotationDialog.validUntil')" required :min="todayIso()" :error="errors.validity" />

        <div class="flex flex-col gap-3">
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium text-text-secondary">{{ t('project.newQuotationDialog.lineItems') }}</label>
            <BaseButton variant="ghost" size="sm" :icon="Plus" @click="addLineItem">{{ t('project.newQuotationDialog.addLineItem') }}</BaseButton>
          </div>

          <div class="overflow-x-auto rounded-lg border border-border-light">
            <table class="w-full min-w-[560px] border-collapse">
              <thead>
                <tr class="border-b border-border-light bg-bg-secondary">
                  <th class="px-3 py-2.5 text-start text-xs font-semibold uppercase tracking-wide text-text-muted">
                    {{ t('project.newQuotationDialog.columnLineItem') }}
                  </th>
                  <th class="w-24 px-3 py-2.5 text-end text-xs font-semibold uppercase tracking-wide text-text-muted">
                    {{ t('project.newQuotationDialog.columnQty') }}
                  </th>
                  <th class="w-32 px-3 py-2.5 text-end text-xs font-semibold uppercase tracking-wide text-text-muted">
                    {{ t('project.newQuotationDialog.columnRate') }}
                  </th>
                  <th class="w-32 px-3 py-2.5 text-end text-xs font-semibold uppercase tracking-wide text-text-muted">
                    {{ t('project.newQuotationDialog.columnAmount') }}
                  </th>
                  <th class="w-10 px-2 py-2.5"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in form.lineItems" :key="index" class="border-b border-border-light last:border-0">
                  <td class="px-3 py-2 align-top">
                    <TextInput v-model="item.description" :placeholder="t('project.newQuotationDialog.descriptionPlaceholder')" :error="lineItemErrors[index]?.description" />
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
                      :model-value="item.unitPrice"
                      :min="0"
                      step="0.01"
                      :error="lineItemErrors[index]?.unitPrice"
                      @update:model-value="item.unitPrice = Number($event)"
                    />
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

        <NumberInput
          :model-value="form.discountAmount"
          :label="t('project.newQuotationDialog.discountAmount')"
          :min="0"
          step="0.01"
          :error="errors.discountAmount"
          @update:model-value="form.discountAmount = Number($event)"
        />

        <TextArea v-model="form.notes" :label="t('project.newQuotationDialog.notes')" :placeholder="t('project.newQuotationDialog.notesPlaceholder')" :rows="2" />
        <TextArea
          v-model="form.scopePhasesText"
          :label="t('project.newQuotationDialog.scopePhases')"
          :placeholder="t('project.newQuotationDialog.scopePhasesPlaceholder')"
          :hint="t('project.newQuotationDialog.scopePhasesHint')"
          :rows="3"
        />
        <TextArea
          v-model="form.paymentTermsText"
          :label="t('project.newQuotationDialog.paymentTerms')"
          :placeholder="t('project.newQuotationDialog.paymentTermsPlaceholder')"
          :hint="t('project.newQuotationDialog.paymentTermsHint')"
          :rows="3"
        />
        <TextArea
          v-model="form.termsText"
          :label="t('project.newQuotationDialog.termsAndConditions')"
          :placeholder="t('project.newQuotationDialog.termsPlaceholder')"
          :hint="t('project.newQuotationDialog.termsHint')"
          :rows="3"
        />

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
      </div>

      <div class="mt-6 flex justify-end gap-3">
        <BaseButton variant="secondary" :disabled="isSubmitting" @click="goBack">{{ t('common.cancel') }}</BaseButton>
        <BaseButton :loading="isSubmitting" @click="handleSubmit">{{ t('project.newQuotationDialog.createQuotation') }}</BaseButton>
      </div>
    </div>
  </div>
</template>
