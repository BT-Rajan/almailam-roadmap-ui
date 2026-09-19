<script setup lang="ts">
import { ArrowRight, Eye, FileSignature, FileText, Wallet } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import CustomerIdDocumentCard from '@/components/document/CustomerIdDocumentCard.vue'
import SubmissionFilesList from '@/components/government/SubmissionFilesList.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { documentTemplateService } from '@/services/documentTemplateService'
import { governmentSubmissionService } from '@/services/governmentSubmissionService'
import { useClientStore } from '@/stores/clientStore'
import { useContractStore } from '@/stores/contractStore'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { usePaymentStore } from '@/stores/paymentStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import { useToastStore } from '@/stores/toastStore'
import type { ClientDocument } from '@/types/Client'
import type { AgreementStream } from '@/types/Payment'
import type { Project } from '@/types/Project'
import type { GovernmentSubmission, SubmissionFollowup } from '@/types/Submission'
import { openBlobInWindow } from '@/utils/fileDownload'
import { buildSubmissionFiles } from '@/utils/submissionFiles'
import type { SubmissionFile } from '@/utils/submissionFiles'
import { getSubmissionStageVariant } from '@/utils/submissionHelpers'

const props = defineProps<{
  project: Project
}>()

const clientStore = useClientStore()
const contractStore = useContractStore()
const governmentSubmissionStore = useGovernmentSubmissionStore()
const router = useRouter()
const paymentStore = usePaymentStore()
const quotationStore = useQuotationStore()
const resultDialogStore = useResultDialogStore()
const toastStore = useToastStore()
const { t } = useI18n()

// A read-only, view-only summary of a project's system-generated
// paperwork -- client ID, accepted quotation, payment plan(s), accepted
// contract -- each opened as a PDF, same "print" mechanism as those
// documents' own tabs use. Lives on the Scope tab (reachable via the
// Workflow Progress stepper regardless of the project's current stage,
// same as Overview), so it's a fixed place to check back on as each
// document becomes available, rather than only late in the project's
// life. No edit/delete here: this is a snapshot for reference, not
// another place to manage them from.

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

// Permit application files -- everything uploaded against this project's
// permit applications (required documents, the filing acknowledgement,
// follow-up documents, the authority's response), grouped by
// application, each with a view link. Fetched fresh whenever this tab
// opens, so a file uploaded on an application's own page shows up here
// straight away. Applications with nothing uploaded yet are left out.
interface PermitApplicationFiles {
  submission: GovernmentSubmission
  files: SubmissionFile[]
}

const permitApplications = ref<PermitApplicationFiles[]>([])
const isLoadingPermitFiles = ref(false)

const permitFileLabels = computed(() => ({
  acknowledgement: t('government.workspacePage.acknowledgementFileLabel'),
  followup: t('government.workspacePage.followUpFileLabel'),
  response: t('government.workspacePage.authorityResponse'),
}))

async function loadPermitFiles(): Promise<void> {
  const projectId = props.project.id
  isLoadingPermitFiles.value = true
  try {
    const submissions = await governmentSubmissionService.getSubmissions(projectId)
    const groups = await Promise.all(
      submissions.map(async (submission): Promise<PermitApplicationFiles> => {
        let followups: SubmissionFollowup[] = []
        // Follow-ups only exist from Track onward.
        if (submission.stage === 'Track' || submission.stage === 'Close') {
          try {
            followups = await governmentSubmissionService.getFollowups(submission.submissionNo)
          } catch {
            followups = []
          }
        }
        return { submission, files: buildSubmissionFiles(submission, followups, permitFileLabels.value) }
      }),
    )
    if (projectId !== props.project.id) return
    permitApplications.value = groups.filter((group) => group.files.length > 0)
  } catch {
    if (projectId === props.project.id) permitApplications.value = []
  } finally {
    if (projectId === props.project.id) isLoadingPermitFiles.value = false
  }
}
onMounted(loadPermitFiles)
watch(() => props.project.id, loadPermitFiles)

// What each application group is headed with: the form it's for, when
// the store already has the forms loaded (it does once the Approvals &
// Permits card has been visited), else just its number.
function permitApplicationTitle(submission: GovernmentSubmission): string {
  const formTitle = governmentSubmissionStore.getFormById(submission.formId)?.title
  return formTitle ? `${submission.submissionNo} · ${formTitle}` : submission.submissionNo
}

function openPermitApplication(submissionNo: string): void {
  router.push({
    name: ROUTE_NAMES.PROJECT_SUBMISSION_WORKSPACE,
    params: { projectId: props.project.id, submissionNo },
    query: { tab: 'overview' },
  })
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

    <div class="flex flex-col gap-3">
      <h3 class="text-sm font-semibold text-text-primary">{{ t('project.contractDocumentsTab.permitFilesTitle') }}</h3>
      <div v-if="isLoadingPermitFiles && permitApplications.length === 0" class="rounded-xl border border-border-light bg-bg-card p-5">
        <SkeletonLoader :rows="2" />
      </div>
      <EmptyState v-else-if="permitApplications.length === 0" :title="t('project.contractDocumentsTab.noPermitFiles')" />
      <template v-else>
        <Card v-for="group in permitApplications" :key="group.submission.submissionNo" :padded="false">
          <template #header>
            <div class="flex items-center justify-between gap-3">
              <div class="flex min-w-0 items-center gap-2">
                <p class="truncate text-sm font-semibold text-text-primary">{{ permitApplicationTitle(group.submission) }}</p>
                <StatusBadge :label="t(`government.submissionStage.${group.submission.stage.toLowerCase()}`)" :variant="getSubmissionStageVariant(group.submission.stage)" />
              </div>
              <BaseButton size="sm" variant="ghost" :icon="ArrowRight" class="shrink-0 no-print" @click="openPermitApplication(group.submission.submissionNo)">
                {{ t('project.contractDocumentsTab.openApplication') }}
              </BaseButton>
            </div>
          </template>
          <SubmissionFilesList :files="group.files" />
        </Card>
      </template>
    </div>
  </div>
</template>
