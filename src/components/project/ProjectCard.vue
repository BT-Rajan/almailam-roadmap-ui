<script setup lang="ts">
import { Building2, CalendarClock, FileSignature, FileText, UserRound, Wallet } from '@lucide/vue'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import IconButton from '@/components/common/IconButton.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { contractService } from '@/services/contractService'
import { documentTemplateService } from '@/services/documentTemplateService'
import { paymentService } from '@/services/paymentService'
import { quotationService } from '@/services/quotationService'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type { Client } from '@/types/Client'
import type { Project } from '@/types/Project'
import { formatDate } from '@/utils/dateFormatter'
import { openBlobInWindow } from '@/utils/fileDownload'
import { getProjectStatusVariant, getWorkflowStageLabel } from '@/utils/projectHelpers'

const props = defineProps<{
  project: Project
  client?: Client
  // Adds the Quotation/Payment Plan/Contract "view PDF" row below --
  // off by default since this card is also used on the main Projects
  // browse page (ProjectsPage.vue), where a client's own paperwork
  // isn't the point and three more icons per card would just be noise.
  // Only ClientWorkspacePage's Projects tab turns this on, where
  // they're the reason for the row (see that page's comment on why:
  // opening this project properly always lands on Requirement/Overview
  // regardless of stage, per ProjectWorkspacePage's own "exactly one
  // way to land on a project" rule, so these are the one place you can
  // jump straight to a specific document without a detour).
  showDocumentLinks?: boolean
}>()

const emit = defineEmits<{
  open: [projectId: string]
}>()

const { t } = useI18n()
const resultDialogStore = useResultDialogStore()

const clientName = computed(() => props.client?.companyName ?? t('project.unknownClient'))

function open(): void {
  emit('open', props.project.id)
}

const STAGE_LABEL_KEYS: Record<string, string> = {
  Requirement: 'project.stage.requirement',
  Quotation: 'project.stage.quotation',
  'Payment Plan': 'project.stage.paymentPlan',
  Contract: 'project.stage.contract',
  Design: 'project.stage.design',
  Supervision: 'project.stage.supervision',
  'Government Submission': 'project.stage.governmentSubmission',
  Handover: 'project.stage.handover',
}
const stageLabel = computed(() => t(STAGE_LABEL_KEYS[props.project.currentStage] ?? getWorkflowStageLabel(props.project.currentStage)))

const STATUS_LABEL_KEYS: Record<string, string> = {
  Active: 'project.status.active',
  'On Hold': 'project.status.onHold',
  Cancelled: 'project.status.cancelled',
  Completed: 'project.status.completed',
}
const statusLabel = computed(() => t(STATUS_LABEL_KEYS[props.project.status] ?? props.project.status))

function handleKeydown(event: KeyboardEvent): void {
  // See ClientCard.vue's identical fix: the whole card acts as one big
  // button, so Enter and Space both activate it -- a mouse-only @click
  // here would otherwise make every project in the grid unreachable to
  // keyboard and screen-reader users entirely.
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    open()
  }
}

// Same "open a blank tab synchronously, fill it once the PDF is fetched"
// dance, and the same fetch-the-latest-then-view-its-PDF flow, as
// ContractDocumentsTab.vue's identical three functions -- duplicated
// rather than shared because that version already has its one
// project's quotation/contract/agreement preloaded in the page-level
// stores, while this card (used in a multi-project list) doesn't, and
// fetches each on demand instead.
const isOpeningQuotation = ref(false)
async function viewQuotationPdf(event: MouseEvent): Promise<void> {
  event.stopPropagation()
  const printWindow = window.open('', '_blank')
  isOpeningQuotation.value = true
  try {
    const quotations = await quotationService.getQuotationsByProject(props.project.id)
    const latest = [...quotations].sort((a, b) => b.issueDate.localeCompare(a.issueDate))[0]
    if (!latest) {
      printWindow?.close()
      return
    }
    const blob = await documentTemplateService.getQuotationDocumentPdf(latest.id)
    openBlobInWindow(blob, printWindow)
  } catch (error) {
    printWindow?.close()
    resultDialogStore.showError(t('common.failedToGenerateDocument'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isOpeningQuotation.value = false
  }
}

const isOpeningPaymentPlan = ref(false)
async function viewPaymentPlanPdf(event: MouseEvent): Promise<void> {
  event.stopPropagation()
  const printWindow = window.open('', '_blank')
  isOpeningPaymentPlan.value = true
  try {
    const agreement = await paymentService.getAgreementByProject(props.project.id)
    if (!agreement) {
      printWindow?.close()
      return
    }
    const blob = await documentTemplateService.getPaymentPlanDocumentPdf(props.project.projectNo)
    openBlobInWindow(blob, printWindow)
  } catch (error) {
    printWindow?.close()
    resultDialogStore.showError(t('common.failedToGenerateDocument'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isOpeningPaymentPlan.value = false
  }
}

const isOpeningContract = ref(false)
async function viewContractPdf(event: MouseEvent): Promise<void> {
  event.stopPropagation()
  const printWindow = window.open('', '_blank')
  isOpeningContract.value = true
  try {
    const contracts = await contractService.getContractsByProject(props.project.id)
    const latest = [...contracts].sort((a, b) => b.issueDate.localeCompare(a.issueDate))[0]
    if (!latest) {
      printWindow?.close()
      return
    }
    const blob = await documentTemplateService.getContractDocumentPdf(latest.id)
    openBlobInWindow(blob, printWindow)
  } catch (error) {
    printWindow?.close()
    resultDialogStore.showError(t('common.failedToGenerateDocument'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isOpeningContract.value = false
  }
}
</script>

<template>
  <Card
    hoverable
    class="cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500"
    role="button"
    tabindex="0"
    :aria-label="t('project.card.openProject', { name: project.projectName })"
    @click="open"
    @keydown="handleKeydown"
  >
    <div class="flex flex-col gap-4">
      <div class="flex items-start justify-between gap-3">
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ project.projectNo }}</p>
          <h3 class="text-base font-semibold leading-snug text-text-primary">{{ project.projectName }}</h3>
        </div>
        <StatusBadge :label="statusLabel" :variant="getProjectStatusVariant(project.status)" show-dot />
      </div>

      <div class="flex items-center gap-2 text-sm text-text-muted">
        <Building2 class="h-4 w-4 shrink-0 text-text-muted" />
        <span class="truncate">{{ clientName }}</span>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <StatusBadge :label="stageLabel" variant="info" />
      </div>

      <ProgressBar :value="project.progress" show-label />

      <div class="flex items-center justify-between border-t border-border-light pt-3 text-xs text-text-muted">
        <div class="flex items-center gap-1.5">
          <UserRound class="h-3.5 w-3.5" />
          <span>{{ project.engineer }}</span>
        </div>
        <div class="flex items-center gap-1.5">
          <CalendarClock class="h-3.5 w-3.5" />
          <span>{{ formatDate(project.targetDate) }}</span>
        </div>
      </div>

      <div v-if="showDocumentLinks" class="flex items-center justify-end gap-1 border-t border-border-light pt-3">
        <IconButton
          :icon="FileText"
          :label="t('project.contractDocumentsTab.quotation') + ' \u2013 ' + t('document.card.viewDocument')"
          size="sm"
          :disabled="isOpeningQuotation"
          @click="viewQuotationPdf"
        />
        <IconButton
          :icon="Wallet"
          :label="t('project.contractDocumentsTab.paymentPlan') + ' \u2013 ' + t('document.card.viewDocument')"
          size="sm"
          :disabled="isOpeningPaymentPlan"
          @click="viewPaymentPlanPdf"
        />
        <IconButton
          :icon="FileSignature"
          :label="t('project.contractDocumentsTab.contract') + ' \u2013 ' + t('document.card.viewDocument')"
          size="sm"
          :disabled="isOpeningContract"
          @click="viewContractPdf"
        />
      </div>
    </div>
  </Card>
</template>
