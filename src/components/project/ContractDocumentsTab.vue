<script setup lang="ts">
import { Eye, FileSignature, FileText, Wallet } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'
import CustomerIdDocumentCard from '@/components/document/CustomerIdDocumentCard.vue'
import { documentTemplateService } from '@/services/documentTemplateService'
import { useClientStore } from '@/stores/clientStore'
import { useContractStore } from '@/stores/contractStore'
import { usePaymentStore } from '@/stores/paymentStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import { useToastStore } from '@/stores/toastStore'
import type { ClientDocument } from '@/types/Client'
import type { Project } from '@/types/Project'
import { openBlobInWindow } from '@/utils/fileDownload'

const props = defineProps<{
  project: Project
}>()

const clientStore = useClientStore()
const contractStore = useContractStore()
const paymentStore = usePaymentStore()
const quotationStore = useQuotationStore()
const resultDialogStore = useResultDialogStore()
const toastStore = useToastStore()
const { t } = useI18n()

// A read-only summary of the paperwork a Contract-stage project has
// produced so far -- client ID, quotation, payment plan, contract --
// each opened as a PDF, same "print" mechanism as those documents' own
// tabs use. No edit/delete here: this is a snapshot for reference, not
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

const hasAnyAgreement = computed(() => paymentStore.agreements.some((agreement) => agreement.projectId === props.project.id))

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

const isOpeningPaymentPlan = ref(false)
async function viewPaymentPlanPdf(): Promise<void> {
  const printWindow = window.open('', '_blank')
  isOpeningPaymentPlan.value = true
  try {
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
                <p class="text-sm font-semibold text-text-primary">{{ t('project.contractDocumentsTab.paymentPlan') }}</p>
                <p class="text-xs text-text-muted">
                  {{ hasAnyAgreement ? project.projectNo : t('project.contractDocumentsTab.notAvailable') }}
                </p>
              </div>
            </div>
            <IconButton
              :icon="Eye"
              :label="t('document.card.viewDocument')"
              size="sm"
              :disabled="!hasAnyAgreement || isOpeningPaymentPlan"
              @click="viewPaymentPlanPdf"
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
  </div>
</template>
