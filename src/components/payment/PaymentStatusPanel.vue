<script setup lang="ts">
import { Banknote, Wallet } from '@lucide/vue'
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextInput from '@/components/common/TextInput.vue'
import { usePaymentAgreements } from '@/composables/usePaymentAgreements'
import { usePaymentStore } from '@/stores/paymentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import { formatCurrency } from '@/utils/currencyFormatter'
import { getAgreementStreamLabel, getObligationAmountPending } from '@/utils/paymentHelpers'
import type { Client } from '@/types/Client'
import type { AgreementStream, PaymentMode, RecordPaymentInput } from '@/types/Payment'
import type { Project, ProjectWorkspaceTabKey } from '@/types/Project'
import type { SelectOption } from '@/types/Ui'

interface Props {
  projectId: string
  project: Project
  client: Client | undefined
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
  'add-service': []
}>()

const { visibleStreams, agreementForStream, outstandingObligationsForStream, summaryForStream } = usePaymentAgreements(
  () => props.projectId,
  () => props.project,
)

const store = usePaymentStore()
const projectStore = useProjectStore()
const resultDialogStore = useResultDialogStore()
const { t } = useI18n()

const AGREEMENT_STATUS_LABEL_KEYS: Record<string, string> = {
  Draft: 'payment.agreementStatus.draft',
  Approved: 'payment.agreementStatus.approved',
}
function agreementStatusLabel(status: string): string {
  return t(AGREEMENT_STATUS_LABEL_KEYS[status] ?? status)
}

const AGREEMENT_STREAM_LABEL_KEYS: Record<string, string> = {
  Design: 'payment.agreementStream.design',
  Supervision: 'payment.agreementStream.supervision',
}
function agreementStreamLabel(stream: string): string {
  return t(AGREEMENT_STREAM_LABEL_KEYS[stream] ?? getAgreementStreamLabel(stream as AgreementStream))
}

// Just the 3 modes staff actually record payments against here --
// PAYMENT_MODES itself (backend/app/models/payment.py) still has the
// other 4 (Bank Transfer, Credit Card, Debit Card, Other) for other
// contexts (e.g. an agreement's own default payment_mode), this screen
// just doesn't offer them as a payment-entry choice.
const PAYMENT_MODE_OPTIONS: SelectOption[] = [
  { label: 'Cash', value: 'Cash', labelKey: 'payment.paymentMode.cash' },
  { label: 'Cheque', value: 'Cheque', labelKey: 'payment.paymentMode.cheque' },
  { label: 'Online Payment', value: 'Online Payment', labelKey: 'payment.paymentMode.onlinePayment' },
]

const streamsWithAgreement = () => visibleStreams.value.filter((stream) => agreementForStream(stream))
const streamsMissingAgreement = () => visibleStreams.value.filter((stream) => !agreementForStream(stream))

// The earliest not-yet-settled installment on this stream's schedule --
// "Expected Amount" mirrors this so staff see what's actually due before
// typing in what was received, same "oldest obligation first" ordering
// the submit below allocates against.
function nextObligationFor(stream: AgreementStream) {
  return outstandingObligationsForStream(stream)
    .slice()
    .sort((a, b) => a.sequenceNumber - b.sequenceNumber)[0]
}
function expectedAmountFor(stream: AgreementStream): number {
  const next = nextObligationFor(stream)
  return next ? getObligationAmountPending(next) : 0
}

interface EntryForm {
  paymentDate: string
  paymentMode: PaymentMode
  referenceNumber: string
  actualAmount: number
}

function freshForm(stream: AgreementStream): EntryForm {
  return {
    paymentDate: new Date().toISOString().slice(0, 10),
    paymentMode: 'Cash',
    referenceNumber: '',
    actualAmount: expectedAmountFor(stream),
  }
}

// One independent form per stream -- a project can be recording a
// Design payment and a Supervision payment at the same time.
const forms = reactive<Partial<Record<AgreementStream, EntryForm>>>({})
function formFor(stream: AgreementStream): EntryForm {
  const existing = forms[stream]
  if (existing) return existing
  const created = freshForm(stream)
  forms[stream] = created
  return created
}

// Applied automatically, oldest outstanding obligation first -- staff
// enter what was actually received, not which installment(s) it
// settles.
function allocationsFor(stream: AgreementStream, amount: number) {
  const obligations = outstandingObligationsForStream(stream)
    .slice()
    .sort((a, b) => a.sequenceNumber - b.sequenceNumber)
  let remaining = amount
  const result: { obligationId: string; amount: number }[] = []
  for (const obligation of obligations) {
    if (remaining <= 0) break
    const allocated = Math.round(Math.min(getObligationAmountPending(obligation), remaining) * 100) / 100
    if (allocated > 0) result.push({ obligationId: obligation.id, amount: allocated })
    remaining = Math.round((remaining - allocated) * 100) / 100
  }
  return result
}

function totalOutstandingFor(stream: AgreementStream): number {
  return Math.round(
    outstandingObligationsForStream(stream).reduce((sum, obligation) => sum + getObligationAmountPending(obligation), 0) * 100,
  ) / 100
}

function canSubmitFor(stream: AgreementStream): boolean {
  const form = formFor(stream)
  return form.actualAmount > 0 && form.actualAmount <= totalOutstandingFor(stream) + 0.009
}

function receivableFor(stream: AgreementStream): number {
  const summary = summaryForStream(stream)
  if (!summary) return 0
  return Math.round((summary.contractAmount - summary.totalReceived) * 100) / 100
}

const submittingStream = ref<AgreementStream | undefined>(undefined)

async function handleRecordPayment(stream: AgreementStream): Promise<void> {
  const agreement = agreementForStream(stream)
  const form = formFor(stream)
  if (!agreement || !canSubmitFor(stream)) return
  submittingStream.value = stream
  try {
    const input: RecordPaymentInput = {
      agreementId: agreement.id,
      projectId: props.projectId,
      amountReceived: form.actualAmount,
      paymentDate: form.paymentDate,
      paymentMode: form.paymentMode,
      referenceNumber: form.referenceNumber.trim() || undefined,
      payer: props.client?.companyName || props.project.projectName,
      allocations: allocationsFor(stream, form.actualAmount),
    }
    await store.recordPayment(input, 'Rajan Kumar')
    // Keeps the shared project store's cached data (e.g. amounts shown
    // elsewhere in the workspace) in sync with what was just recorded.
    await projectStore.refreshProject(props.projectId)
    resultDialogStore.showSuccess(t('payment.statusPanel.paymentRecordedTitle'), t('payment.statusPanel.paymentRecordedDescription'))
    forms[stream] = freshForm(stream)
  } catch (error) {
    resultDialogStore.showError(t('payment.statusPanel.couldNotRecordPayment'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    submittingStream.value = undefined
  }
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <EmptyState
      v-if="visibleStreams.length === 0"
      :icon="Wallet"
      :title="t('payment.statusPanel.noBillableTitle')"
      :description="t('payment.statusPanel.noBillableDescription')"
      :action-label="t('payment.statusPanel.addService')"
      @action="emit('add-service')"
    />

    <EmptyState
      v-else-if="streamsWithAgreement().length === 0"
      :icon="Wallet"
      :title="t('payment.statusPanel.noPlanDefinedTitle')"
      :description="t('payment.statusPanel.noPlanDefinedDescription')"
      :action-label="t('payment.statusPanel.goToPaymentPlan')"
      @action="emit('navigate-tab', 'payment-plan')"
    />

    <template v-else>
      <p v-if="streamsMissingAgreement().length > 0" class="text-sm text-text-muted">
        {{ t('payment.statusPanel.missingPlanNotice', { streams: streamsMissingAgreement().map((s) => agreementStreamLabel(s)).join(' and ') }) }}
        <button type="button" class="text-accent-600 underline" @click="emit('navigate-tab', 'payment-plan')">{{ t('payment.statusPanel.missingPlanLink') }}</button>.
      </p>

      <div v-for="stream in streamsWithAgreement()" :key="stream" class="flex flex-col gap-4">
        <div v-if="streamsWithAgreement().length > 1" class="flex items-center gap-2">
          <h3 class="text-sm font-semibold uppercase tracking-wide text-text-muted">{{ agreementStreamLabel(stream) }}</h3>
          <StatusBadge
            :label="agreementStatusLabel(agreementForStream(stream)!.status)"
            :variant="agreementForStream(stream)!.status === 'Approved' ? 'success' : 'warning'"
          />
        </div>

        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
          <div class="rounded-lg border border-border-light p-4">
            <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('payment.statusPanel.totalContractAmount') }}</p>
            <p class="text-lg font-semibold text-text-primary">{{ formatCurrency(summaryForStream(stream)!.contractAmount, agreementForStream(stream)!.currency) }}</p>
          </div>
          <div class="rounded-lg border border-border-light p-4">
            <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('payment.statusPanel.totalReceived') }}</p>
            <p class="text-lg font-semibold text-success-600">{{ formatCurrency(summaryForStream(stream)!.totalReceived, agreementForStream(stream)!.currency) }}</p>
          </div>
          <div class="rounded-lg border border-border-light p-4">
            <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('payment.statusPanel.totalReceivable') }}</p>
            <p class="text-lg font-semibold text-text-primary">{{ formatCurrency(receivableFor(stream), agreementForStream(stream)!.currency) }}</p>
          </div>
        </div>

        <Card>
          <template #header>
            <h4 class="text-sm font-semibold text-text-primary">{{ t('payment.statusPanel.recordPayment') }}</h4>
          </template>

          <div v-if="totalOutstandingFor(stream) <= 0" class="text-sm text-text-muted">
            {{ t('payment.statusPanel.fullySettled') }}
          </div>
          <div v-else class="flex flex-col gap-4">
            <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
              <DatePicker v-model="formFor(stream).paymentDate" :label="t('payment.statusPanel.paymentDate')" required />
              <SelectBox
                :model-value="formFor(stream).paymentMode"
                :label="t('payment.statusPanel.paymentMode')"
                :options="PAYMENT_MODE_OPTIONS"
                @update:model-value="formFor(stream).paymentMode = $event as PaymentMode"
              />
              <TextInput
                v-model="formFor(stream).referenceNumber"
                :label="t('payment.statusPanel.referenceNumber')"
                :placeholder="t('payment.statusPanel.referenceNumberPlaceholder')"
              />
              <div class="flex flex-col gap-1.5">
                <label class="text-sm font-medium text-text-secondary">{{ t('payment.statusPanel.expectedAmount') }}</label>
                <p class="rounded-lg border border-border-light bg-bg-secondary px-3 py-2 text-sm text-text-secondary">
                  {{ formatCurrency(expectedAmountFor(stream), agreementForStream(stream)!.currency) }}
                </p>
              </div>
              <NumberInput
                :model-value="formFor(stream).actualAmount"
                :label="t('payment.statusPanel.actualAmount')"
                :min="0"
                step="0.01"
                required
                :error="
                  formFor(stream).actualAmount > totalOutstandingFor(stream) + 0.009
                    ? t('payment.statusPanel.exceedsOutstanding', { amount: formatCurrency(totalOutstandingFor(stream), agreementForStream(stream)!.currency) })
                    : undefined
                "
                @update:model-value="formFor(stream).actualAmount = Number($event)"
              />
            </div>

            <div class="flex justify-end">
              <BaseButton
                size="sm"
                :icon="Banknote"
                :loading="submittingStream === stream"
                :disabled="!canSubmitFor(stream)"
                @click="handleRecordPayment(stream)"
              >
                {{ t('payment.statusPanel.recordPayment') }}
              </BaseButton>
            </div>
          </div>
        </Card>
      </div>
    </template>
  </div>
</template>
