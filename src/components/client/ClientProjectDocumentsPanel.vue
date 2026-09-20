<script setup lang="ts">
import { FileSignature, FileText, FolderCheck, Wallet } from '@lucide/vue'
import { computed, onMounted, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PaginatedList from '@/components/common/PaginatedList.vue'
import IconButton from '@/components/common/IconButton.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import { contractService } from '@/services/contractService'
import { documentService } from '@/services/documentService'
import { documentTemplateService } from '@/services/documentTemplateService'
import { paymentService } from '@/services/paymentService'
import { quotationService } from '@/services/quotationService'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type { Project } from '@/types/Project'
import { formatDate } from '@/utils/dateFormatter'
import { openBlobInWindow } from '@/utils/fileDownload'

const props = withDefaults(
  defineProps<{
    projects: Project[]
    // Set from ClientDocumentsDialog.vue, which already gives this its
    // own dialog chrome -- avoids a card-inside-a-card look. The
    // standalone Card wrapper stays the default for any other caller
    // (e.g. ClientWorkspacePage's Overview tab).
    bare?: boolean
  }>(),
  { bare: false },
)

const { t } = useI18n()
const resultDialogStore = useResultDialogStore()

// One entry per project, populated as each project's own set of fetches
// resolves -- undefined while loading, so a client with several projects
// shows each project's section settle independently rather than the
// whole panel blocking on the slowest one. Each item carries the date
// that document itself is dated by (issue/agreement/upload date), not
// just whether it exists.
interface ProjectDocsAvailability {
  quotation: { id: string; date: string } | null
  agreement: { date: string } | null
  contract: { id: string; date: string } | null
  handoverDocuments: { id: string; date: string }[]
}
const availability = reactive<Record<string, ProjectDocsAvailability | undefined>>({})
const loadingIds = reactive<Set<string>>(new Set())

// Sorted so "arranged by project" is a stable, predictable order (project
// number) rather than whatever order the client's project list happened
// to load in.
const sortedProjects = computed(() => [...props.projects].sort((a, b) => a.projectNo.localeCompare(b.projectNo)))

async function loadForProject(project: Project): Promise<void> {
  if (availability[project.id] || loadingIds.has(project.id)) return
  loadingIds.add(project.id)
  try {
    const [quotations, contracts, agreement, documents] = await Promise.all([
      quotationService.getQuotationsByProject(project.id),
      contractService.getContractsByProject(project.id),
      paymentService.getAgreementByProject(project.id).catch(() => undefined),
      documentService.getDocumentsByProject(project.id),
    ])

    // "Signed" quotation/contract -- the most recent one that has
    // actually left Draft, not merely the most recent of any status
    // (a newer Draft revision sitting on top of an already-Approved one
    // shouldn't hide the signed copy that's still the operative one).
    const signedQuotation = [...quotations]
      .filter((q) => q.status === 'Approved')
      .sort((a, b) => b.issueDate.localeCompare(a.issueDate))[0]
    const signedContract = [...contracts]
      .filter((c) => c.status !== 'Draft')
      .sort((a, b) => b.issueDate.localeCompare(a.issueDate))[0]
    const handoverDocuments = documents
      .filter((d) => d.type === 'Report' && d.title.startsWith('Signed Hand-over Acknowledgment'))
      .sort((a, b) => b.uploadDate.localeCompare(a.uploadDate))

    availability[project.id] = {
      quotation: signedQuotation ? { id: signedQuotation.id, date: signedQuotation.issueDate } : null,
      agreement: agreement?.status === 'Approved' ? { date: agreement.agreementDate } : null,
      contract: signedContract ? { id: signedContract.id, date: signedContract.signedDate ?? signedContract.issueDate } : null,
      handoverDocuments: handoverDocuments.map((d) => ({ id: d.id, date: d.uploadDate })),
    }
  } catch {
    // Leave this project's row out rather than surfacing a fetch error
    // for what is, for the person looking at it, a purely informational
    // "here's what's ready" list -- ProjectCard's own view actions (still
    // reachable from the Projects tab) already report load failures.
    availability[project.id] = { quotation: null, agreement: null, contract: null, handoverDocuments: [] }
  } finally {
    loadingIds.delete(project.id)
  }
}

function loadAll(): void {
  for (const project of props.projects) void loadForProject(project)
}

onMounted(loadAll)
watch(() => props.projects.map((p) => p.id).join(','), loadAll)

// The list is paged by document, not by project: a project can carry
// several documents (any number of signed hand-over acknowledgments), so
// paging by project would still leave one project's section unbounded.
// Every project contributes at least one row -- a placeholder while its
// documents load, or a "none yet" line once they have -- so it keeps its
// heading and the panel still reads the same for a client with one
// project as for several.
type DocumentKind = 'quotation' | 'paymentPlan' | 'contract' | 'handover'

interface DocumentRow {
  key: string
  project: Project
  state: 'loading' | 'empty' | 'document'
  kind?: DocumentKind
  documentId?: string
  date?: string
}

const DOCUMENT_KINDS: Record<DocumentKind, { icon: typeof FileText; labelKey: string }> = {
  quotation: { icon: FileText, labelKey: 'client.projectDocuments.signedQuotation' },
  paymentPlan: { icon: Wallet, labelKey: 'client.projectDocuments.approvedPaymentPlan' },
  contract: { icon: FileSignature, labelKey: 'client.projectDocuments.signedContract' },
  handover: { icon: FolderCheck, labelKey: 'client.projectDocuments.handoverDocument' },
}

const rows = computed<DocumentRow[]>(() =>
  sortedProjects.value.flatMap((project): DocumentRow[] => {
    if (loadingIds.has(project.id) || !availability[project.id]) return [{ key: `${project.id}:loading`, project, state: 'loading' }]
    const entry = availability[project.id]!
    const documents: DocumentRow[] = []
    if (entry.quotation) documents.push({ key: `${project.id}:quotation`, project, state: 'document', kind: 'quotation', documentId: entry.quotation.id, date: entry.quotation.date })
    if (entry.agreement) documents.push({ key: `${project.id}:paymentPlan`, project, state: 'document', kind: 'paymentPlan', date: entry.agreement.date })
    if (entry.contract) documents.push({ key: `${project.id}:contract`, project, state: 'document', kind: 'contract', documentId: entry.contract.id, date: entry.contract.date })
    for (const handover of entry.handoverDocuments) {
      documents.push({ key: `${project.id}:handover:${handover.id}`, project, state: 'document', kind: 'handover', documentId: handover.id, date: handover.date })
    }
    return documents.length > 0 ? documents : [{ key: `${project.id}:empty`, project, state: 'empty' }]
  }),
)

// One page's rows, regrouped under their project heading (a project whose
// documents straddle two pages simply shows its heading on both).
function groupByProject(pageRows: DocumentRow[]): { project: Project; rows: DocumentRow[] }[] {
  const groups: { project: Project; rows: DocumentRow[] }[] = []
  for (const row of pageRows) {
    const last = groups[groups.length - 1]
    if (last && last.project.id === row.project.id) last.rows.push(row)
    else groups.push({ project: row.project, rows: [row] })
  }
  return groups
}

function openDocument(row: DocumentRow): void {
  if (row.kind === 'quotation' && row.documentId) void viewQuotation(row.documentId)
  else if (row.kind === 'paymentPlan') void viewPaymentPlan(row.project.projectNo)
  else if (row.kind === 'contract' && row.documentId) void viewContract(row.documentId)
  else if (row.kind === 'handover' && row.documentId) void viewHandoverDocument(row.documentId)
}

async function viewQuotation(quotationId: string): Promise<void> {
  const printWindow = window.open('', '_blank')
  try {
    const blob = await documentTemplateService.getQuotationDocumentPdf(quotationId)
    openBlobInWindow(blob, printWindow)
  } catch (error) {
    printWindow?.close()
    resultDialogStore.showError(t('common.failedToGenerateDocument'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  }
}

async function viewPaymentPlan(projectNo: string): Promise<void> {
  const printWindow = window.open('', '_blank')
  try {
    const blob = await documentTemplateService.getPaymentPlanDocumentPdf(projectNo)
    openBlobInWindow(blob, printWindow)
  } catch (error) {
    printWindow?.close()
    resultDialogStore.showError(t('common.failedToGenerateDocument'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  }
}

async function viewContract(contractId: string): Promise<void> {
  const printWindow = window.open('', '_blank')
  try {
    const blob = await documentTemplateService.getContractDocumentPdf(contractId)
    openBlobInWindow(blob, printWindow)
  } catch (error) {
    printWindow?.close()
    resultDialogStore.showError(t('common.failedToGenerateDocument'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  }
}

async function viewHandoverDocument(documentId: string): Promise<void> {
  const printWindow = window.open('', '_blank')
  try {
    const blob = await documentService.downloadDocument(documentId)
    openBlobInWindow(blob, printWindow)
  } catch (error) {
    printWindow?.close()
    resultDialogStore.showError(t('common.failedToGenerateDocument'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  }
}
</script>

<template>
  <component :is="bare ? 'div' : Card">
    <template v-if="!bare" #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ t('client.projectDocuments.title') }}</h3>
    </template>

    <EmptyState
      v-if="sortedProjects.length === 0"
      :icon="FolderCheck"
      :title="t('client.projectDocuments.noProjectsTitle')"
      :description="t('client.projectDocuments.noProjectsDescription')"
    />

    <PaginatedList v-else :items="rows" :page-size="10" stacked>
      <template #default="{ items }">
        <div class="flex flex-col gap-5">
          <div v-for="group in groupByProject(items)" :key="group.project.id" class="flex flex-col gap-2">
            <!-- Project heading -- shown per project even with just one, so
                 the structure reads the same whether a client has one
                 project or several (arranged by project once there's more
                 than one, per the brief). -->
            <p class="text-xs font-medium uppercase tracking-wide text-text-muted">
              {{ group.project.projectNo }} &ndash; {{ group.project.projectName }}
            </p>

            <SkeletonLoader v-if="group.rows[0].state === 'loading'" :rows="2" />

            <p v-else-if="group.rows[0].state === 'empty'" class="text-sm text-text-muted">
              {{ t('client.projectDocuments.noneAvailableYet') }}
            </p>

            <ul v-else class="flex flex-col divide-y divide-border-light rounded-lg border border-border-light">
              <li v-for="row in group.rows" :key="row.key" class="flex items-center justify-between gap-3 px-3 py-2.5">
                <span class="flex flex-col gap-0.5">
                  <span class="inline-flex items-center gap-2 text-sm text-text-primary">
                    <component :is="DOCUMENT_KINDS[row.kind!].icon" class="h-4 w-4 shrink-0 text-text-muted" />
                    {{ t(DOCUMENT_KINDS[row.kind!].labelKey) }}
                  </span>
                  <span class="pl-6 text-xs text-text-muted">{{ formatDate(row.date!) }}</span>
                </span>
                <IconButton :icon="DOCUMENT_KINDS[row.kind!].icon" :label="t('document.card.viewDocument')" size="sm" @click="openDocument(row)" />
              </li>
            </ul>
          </div>
        </div>
      </template>
    </PaginatedList>
  </component>
</template>
