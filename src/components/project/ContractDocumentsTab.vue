<script setup lang="ts">
import { Eye, FileSignature, FileText, Wallet } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseDialog from '@/components/common/BaseDialog.vue'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import CustomerIdDocumentCard from '@/components/document/CustomerIdDocumentCard.vue'
import { documentTemplateService } from '@/services/documentTemplateService'
import { useClientStore } from '@/stores/clientStore'
import { useContractStore } from '@/stores/contractStore'
import { usePaymentStore } from '@/stores/paymentStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import { useStatusReportStore } from '@/stores/statusReportStore'
import { useToastStore } from '@/stores/toastStore'
import type { ClientDocument } from '@/types/Client'
import type { AgreementStream } from '@/types/Payment'
import type { Project } from '@/types/Project'
import type { StatusReport, StatusReportStatus } from '@/types/StatusReport'
import { formatDate } from '@/utils/dateFormatter'
import { openBlobInWindow } from '@/utils/fileDownload'

const props = defineProps<{
  project: Project
}>()

const clientStore = useClientStore()
const contractStore = useContractStore()
const paymentStore = usePaymentStore()
const quotationStore = useQuotationStore()
const resultDialogStore = useResultDialogStore()
const statusReportStore = useStatusReportStore()
const toastStore = useToastStore()
const { t } = useI18n()

// A read-only, view-only summary of a project's system-generated
// paperwork -- client ID, accepted quotation, payment plan(s), accepted
// contract, and (once Supervision is under way) every daily status
// report filed against it -- each opened as a PDF/detail view, same
// "print" mechanism as those documents' own tabs use. Lives on the
// Scope tab (reachable via the Workflow Progress stepper regardless of
// the project's current stage, same as Overview), so it's a fixed
// place to check back on as each document becomes available, rather
// than only late in the project's life. No edit/delete here: this is a
// snapshot for reference, not another place to manage them from.

const identityDocuments = computed<ClientDocument[]>(() =>
  clientStore.documents.filter((document) => document.category === 'Identity Document'),
)

function loadClientDocuments(): void {
  if (props.project.clientId) clientStore.loadClientDetail(props.project.clientId)
}
onMounted(loadClientDocuments)
watch(() => props.project.clientId, loadClientDocuments)

function viewClientDocument(document: ClientDocument): void {
  clientStore.viewDocument(props.project.clientId, document.id).catch(() => {
    toastStore.show('error', t('project.documentsTab.failedToOpenDocument'), t('common.pleaseTryAgain'))
  })
}

// Design and Permit and Supervision are billed as two separate
// FinancialAgreements now (see AGREEMENT_STREAMS) -- shown here as two
// separate payment plan documents rather than one merged file, mirroring
// how the Payment Plan panel itself already splits them into two tabs.
const designAgreement = computed(() => paymentStore.getAgreementByProject(props.project.id, 'Design'))
const supervisionAgreement = computed(() => paymentStore.getAgreementByProject(props.project.id, 'Supervision'))

// Same "open a blank tab synchronously, fill it once the PDF is
// fetched" dance as ProjectQuotationTab.vue/ProjectContractTab.vue's
// own Print actions -- see openBlobInWindow's docstring for why the
// window can't be opened after the await.
const isOpeningQuotation = ref(false)
async function viewQuotationPdf(): Promise<void> {
  const quotation = quotationStore.latestQuotation
  if (!quotation) return
  const printWindow = window.open('', '_blank')
  isOpeningQuotation.value = true
  try {
    const blob = await documentTemplateService.getQuotationDocumentPdf(quotation.id)
    openBlobInWindow(blob, printWindow)
  } catch (error) {
    printWindow?.close()
    resultDialogStore.showError(t('common.failedToGenerateDocument'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isOpeningQuotation.value = false
  }
}

const openingPaymentPlanStream = ref<AgreementStream | null>(null)
async function viewPaymentPlanPdf(stream: AgreementStream): Promise<void> {
  const printWindow = window.open('', '_blank')
  openingPaymentPlanStream.value = stream
  try {
    const blob = await documentTemplateService.getPaymentPlanDocumentPdf(props.project.projectNo, undefined, stream)
    openBlobInWindow(blob, printWindow)
  } catch (error) {
    printWindow?.close()
    resultDialogStore.showError(t('common.failedToGenerateDocument'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    openingPaymentPlanStream.value = null
  }
}

const isOpeningContract = ref(false)
async function viewContractPdf(): Promise<void> {
  const contract = contractStore.latestContract
  if (!contract) return
  const printWindow = window.open('', '_blank')
  isOpeningContract.value = true
  try {
    const blob = await documentTemplateService.getContractDocumentPdf(contract.id)
    openBlobInWindow(blob, printWindow)
  } catch (error) {
    printWindow?.close()
    resultDialogStore.showError(t('common.failedToGenerateDocument'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isOpeningContract.value = false
  }
}

// Every status report the site engineer has ever filed for this
// project -- newest first, as a flat list (unlike SupervisionStatus
// ReportsTab.vue's own calendar, which covers the same data but by
// month) -- linked here automatically the moment it's filed, with
// nothing for staff to upload or attach themselves. Only shown for a
// project that actually includes Supervision; a Design/Government-only
// project has none of these to expect.
function loadStatusReports(): void {
  if (props.project.includesSupervision) void statusReportStore.loadForProject(props.project.projectNo)
}
onMounted(loadStatusReports)
watch(() => props.project.projectNo, loadStatusReports)

const statusReports = computed<StatusReport[]>(() =>
  [...(statusReportStore.projectReports[props.project.projectNo] ?? [])].sort((a, b) => b.reportDate.localeCompare(a.reportDate)),
)

// Same recipient's-eye framing as SupervisionStatusReportsTab.vue's own
// STATUS_LABEL_KEYS -- "Pending Review" / "Reviewed" reads more clearly
// here than the engineer portal's own "Submitted" / "Reviewed" framing.
const STATUS_LABEL_KEYS: Record<StatusReportStatus, string> = {
  Pending: 'project.supervisionReportsTab.statusPendingReview',
  Attached: 'project.supervisionReportsTab.statusReviewed',
}
function reportStatusLabel(status: StatusReportStatus): string {
  return t(STATUS_LABEL_KEYS[status])
}
function reportStatusVariant(status: StatusReportStatus): 'info' | 'success' {
  return status === 'Attached' ? 'success' : 'info'
}

const selectedReport = ref<StatusReport | null>(null)
function viewStatusReport(report: StatusReport): void {
  selectedReport.value = report
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <div class="flex flex-col gap-3">
      <h3 class="text-sm font-semibold text-text-primary">{{ t('project.documentsTab.customerIdTitle') }}</h3>
      <EmptyState
        v-if="identityDocuments.length === 0"
        :title="t('project.documentsTab.noIdentificationDocumentsTitle')"
        :description="t('project.documentsTab.noIdentificationDocumentsDescription')"
      />
      <div v-else class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
        <CustomerIdDocumentCard
          v-for="document in identityDocuments"
          :key="document.id"
          :document="document"
          @view="viewClientDocument"
          @download="viewClientDocument"
        />
      </div>
    </div>

    <div class="flex flex-col gap-3">
      <h3 class="text-sm font-semibold text-text-primary">{{ t('project.contractDocumentsTab.projectPaperworkTitle') }}</h3>
      <Card :padded="false">
        <ul class="flex flex-col divide-y divide-border-light">
          <li class="flex items-center justify-between gap-3 px-5 py-4">
            <div class="flex items-center gap-3">
              <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-700">
                <FileText class="h-5 w-5" />
              </span>
              <div>
                <p class="text-sm font-semibold text-text-primary">{{ t('project.contractDocumentsTab.quotation') }}</p>
                <p class="text-xs text-text-muted">
                  {{ quotationStore.latestQuotation?.quotationNo ?? t('project.contractDocumentsTab.notAvailable') }}
                </p>
              </div>
            </div>
            <IconButton
              :icon="Eye"
              :label="t('document.card.viewDocument')"
              size="sm"
              :disabled="!quotationStore.latestQuotation || isOpeningQuotation"
              @click="viewQuotationPdf"
            />
          </li>
          <li class="flex items-center justify-between gap-3 px-5 py-4">
            <div class="flex items-center gap-3">
              <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-700">
                <Wallet class="h-5 w-5" />
              </span>
              <div>
                <p class="text-sm font-semibold text-text-primary">{{ t('project.contractDocumentsTab.designPaymentPlan') }}</p>
                <p class="text-xs text-text-muted">
                  {{ designAgreement ? project.projectNo : t('project.contractDocumentsTab.notAvailable') }}
                </p>
              </div>
            </div>
            <IconButton
              :icon="Eye"
              :label="t('document.card.viewDocument')"
              size="sm"
              :disabled="!designAgreement || openingPaymentPlanStream === 'Design'"
              @click="viewPaymentPlanPdf('Design')"
            />
          </li>
          <li class="flex items-center justify-between gap-3 px-5 py-4">
            <div class="flex items-center gap-3">
              <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-700">
                <Wallet class="h-5 w-5" />
              </span>
              <div>
                <p class="text-sm font-semibold text-text-primary">{{ t('project.contractDocumentsTab.supervisionPaymentPlan') }}</p>
                <p class="text-xs text-text-muted">
                  {{ supervisionAgreement ? project.projectNo : t('project.contractDocumentsTab.notAvailable') }}
                </p>
              </div>
            </div>
            <IconButton
              :icon="Eye"
              :label="t('document.card.viewDocument')"
              size="sm"
              :disabled="!supervisionAgreement || openingPaymentPlanStream === 'Supervision'"
              @click="viewPaymentPlanPdf('Supervision')"
            />
          </li>
          <li class="flex items-center justify-between gap-3 px-5 py-4">
            <div class="flex items-center gap-3">
              <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-700">
                <FileSignature class="h-5 w-5" />
              </span>
              <div>
                <p class="text-sm font-semibold text-text-primary">{{ t('project.contractDocumentsTab.contract') }}</p>
                <p class="text-xs text-text-muted">
                  {{ contractStore.latestContract?.contractNo ?? t('project.contractDocumentsTab.notAvailable') }}
                </p>
              </div>
            </div>
            <IconButton
              :icon="Eye"
              :label="t('document.card.viewDocument')"
              size="sm"
              :disabled="!contractStore.latestContract || isOpeningContract"
              @click="viewContractPdf"
            />
          </li>
        </ul>
      </Card>
    </div>

    <div v-if="project.includesSupervision" class="flex flex-col gap-3">
      <h3 class="text-sm font-semibold text-text-primary">{{ t('project.contractDocumentsTab.statusReportsTitle') }}</h3>
      <EmptyState
        v-if="statusReports.length === 0"
        :title="t('project.contractDocumentsTab.noStatusReportsTitle')"
        :description="t('project.contractDocumentsTab.noStatusReportsDescription')"
      />
      <Card v-else :padded="false">
        <ul class="flex flex-col divide-y divide-border-light">
          <li v-for="report in statusReports" :key="report.id" class="flex items-center justify-between gap-3 px-5 py-4">
            <div class="flex items-center gap-3">
              <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-700">
                <FileText class="h-5 w-5" />
              </span>
              <div>
                <p class="text-sm font-semibold text-text-primary">{{ formatDate(report.reportDate) }}</p>
                <p class="text-xs text-text-muted">{{ report.engineerName }} · {{ report.reportNo }}</p>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <StatusBadge :label="reportStatusLabel(report.status)" :variant="reportStatusVariant(report.status)" />
              <IconButton :icon="Eye" :label="t('project.contractDocumentsTab.viewReport')" size="sm" @click="viewStatusReport(report)" />
            </div>
          </li>
        </ul>
      </Card>
    </div>

    <BaseDialog :model-value="!!selectedReport" :title="selectedReport?.reportDate ? formatDate(selectedReport.reportDate) : ''" size="md" @update:model-value="selectedReport = null">
      <div v-if="selectedReport" class="flex flex-col gap-3 text-sm">
        <div class="flex items-center justify-between">
          <span class="font-semibold text-text-primary">{{ selectedReport.engineerName }}</span>
          <StatusBadge :label="reportStatusLabel(selectedReport.status)" :variant="reportStatusVariant(selectedReport.status)" />
        </div>
        <div class="flex items-center justify-between">
          <span class="text-text-muted">{{ t('project.supervisionReportsTab.reportNo') }}</span>
          <span class="font-medium text-text-primary">{{ selectedReport.reportNo }}</span>
        </div>
        <div v-if="selectedReport.receiptType" class="flex items-center justify-between">
          <span class="text-text-muted">{{ t('project.supervisionReportsTab.receiptHandover') }}</span>
          <span class="font-medium text-text-primary">{{ selectedReport.receiptType }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-text-muted">{{ t('project.supervisionReportsTab.supervision') }}</span>
          <span class="font-medium text-text-primary">{{ selectedReport.supervisionType }}</span>
        </div>
        <div>
          <p class="mb-1 text-text-muted">{{ t('project.supervisionReportsTab.notes') }}</p>
          <p class="whitespace-pre-wrap rounded-lg bg-bg-secondary p-3 text-text-primary" dir="auto">{{ selectedReport.notes }}</p>
        </div>
      </div>
    </BaseDialog>
  </div>
</template>
