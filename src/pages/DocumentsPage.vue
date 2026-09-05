<script setup lang="ts">
import { LayoutGrid, TableProperties, Upload } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import IconButton from '@/components/common/IconButton.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import DocumentCard from '@/components/document/DocumentCard.vue'
import DocumentUploadDialog from '@/components/document/DocumentUploadDialog.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useDocumentStore } from '@/stores/documentStore'
import { useToastStore } from '@/stores/toastStore'
import type { SmartTableColumn } from '@/types/Table'
import type { DocumentStatus, DocumentType, ProjectDocument } from '@/types/Document'
import type { SelectOption } from '@/types/Ui'
import { formatDate } from '@/utils/dateFormatter'
import { getDocumentStatusVariant } from '@/utils/documentHelpers'

interface DocumentTableRow {
  [key: string]: unknown
  id: string
  title: string
  type: DocumentType
  projectName: string
  revision: string
  uploadedBy: string
  uploadDate: string
  status: DocumentStatus
}

const router = useRouter()
const { t } = useI18n()
const documentStore = useDocumentStore()
const toastStore = useToastStore()

const isUploadDialogOpen = ref(false)

const TYPE_OPTIONS: SelectOption[] = [
  { label: 'All Categories', value: 'All', labelKey: 'document.documentsPage.allCategories' },
  { label: 'Drawing', value: 'Drawing', labelKey: 'document.type.drawing' },
  { label: 'Report', value: 'Report', labelKey: 'document.type.report' },
  { label: 'Contract', value: 'Contract', labelKey: 'document.type.contract' },
  { label: 'Quotation', value: 'Quotation', labelKey: 'document.type.quotation' },
  { label: 'Municipality Form', value: 'Municipality Form', labelKey: 'document.type.municipalityForm' },
  { label: 'Calculation Sheet', value: 'Calculation Sheet', labelKey: 'document.type.calculationSheet' },
  { label: 'Government Agreement', value: 'Government Agreement', labelKey: 'document.type.governmentAgreement' },
]

const STATUS_OPTIONS: SelectOption[] = [
  { label: 'All Statuses', value: 'All', labelKey: 'governmentFormOptions.statusFilter.all' },
  { label: 'Draft', value: 'Draft', labelKey: 'document.status.draft' },
  { label: 'Under Review', value: 'Under Review', labelKey: 'document.status.underReview' },
  { label: 'Approved', value: 'Approved', labelKey: 'document.status.approved' },
  { label: 'Rejected', value: 'Rejected', labelKey: 'document.status.rejected' },
]

const TYPE_LABEL_KEYS: Record<string, string> = {
  Drawing: 'document.type.drawing',
  Report: 'document.type.report',
  Contract: 'document.type.contract',
  Quotation: 'document.type.quotation',
  'Municipality Form': 'document.type.municipalityForm',
  'Calculation Sheet': 'document.type.calculationSheet',
  'Government Agreement': 'document.type.governmentAgreement',
}

const STATUS_LABEL_KEYS: Record<string, string> = {
  Draft: 'document.status.draft',
  'Under Review': 'document.status.underReview',
  Approved: 'document.status.approved',
  Rejected: 'document.status.rejected',
}

function typeLabel(type: string): string {
  const key = TYPE_LABEL_KEYS[type]
  return key ? t(key) : type
}

function statusLabel(status: string): string {
  const key = STATUS_LABEL_KEYS[status]
  return key ? t(key) : status
}

const TABLE_COLUMNS = computed<SmartTableColumn<DocumentTableRow>[]>(() => [
  { key: 'title', label: t('document.documentsPage.columnTitle'), sortable: true },
  { key: 'type', label: t('document.documentsPage.columnCategory'), sortable: true },
  { key: 'projectName', label: t('document.documentsPage.columnProject'), sortable: true },
  { key: 'revision', label: t('document.documentsPage.columnRevision'), sortable: true, width: '110px' },
  { key: 'uploadedBy', label: t('document.documentsPage.columnUploadedBy'), sortable: true },
  { key: 'uploadDate', label: t('document.documentsPage.columnUploadDate'), sortable: true, align: 'right' },
  { key: 'status', label: t('document.documentsPage.columnStatus'), sortable: true },
])

const tableRows = computed<DocumentTableRow[]>(() =>
  documentStore.pageItems.map((document) => ({
    id: document.id,
    title: document.title,
    type: document.type,
    projectName: documentStore.getProjectById(document.projectId)?.projectName ?? t('document.unknownProject'),
    revision: document.revision,
    uploadedBy: document.uploadedBy,
    uploadDate: document.uploadDate,
    status: document.status,
  })),
)

function loadData(): void {
  void documentStore.loadDocumentsPage()
}

onMounted(loadData)

function openDocument(documentId: string): void {
  router.push({ name: ROUTE_NAMES.DOCUMENT_VIEWER, params: { documentId } })
}

function handleUpload(document: ProjectDocument): void {
  toastStore.show('success', 'Document uploaded', `${document.title} was added to the repository.`)
  void documentStore.loadDocumentsPage()
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader :title="t('document.documentsPage.pageTitle')" :subtitle="t('document.documentsPage.pageSubtitle')">
      <template #actions>
        <BaseButton :icon="Upload" @click="isUploadDialogOpen = true">{{ t('document.documentsPage.uploadDocument') }}</BaseButton>
      </template>
    </PageHeader>

    <FilterBar
      :show-search="false"
      :has-active-filters="documentStore.hasActiveFilters"
      @clear="documentStore.clearFilters"
    >
      <template #filters>
        <div class="w-48">
          <SelectBox
            :model-value="documentStore.typeFilter"
            :options="TYPE_OPTIONS"
            @update:model-value="documentStore.setTypeFilter($event as DocumentType | 'All')"
          />
        </div>
        <div class="w-44">
          <SelectBox
            :model-value="documentStore.statusFilter"
            :options="STATUS_OPTIONS"
            @update:model-value="documentStore.setStatusFilter($event as DocumentStatus | 'All')"
          />
        </div>
      </template>
      <template #actions>
        <div class="flex items-center gap-1 rounded-lg border border-border-default p-1">
          <IconButton
            :icon="LayoutGrid"
            :label="t('document.documentsPage.gridView')"
            size="sm"
            :variant="documentStore.viewMode === 'grid' ? 'primary' : 'ghost'"
            @click="documentStore.setViewMode('grid')"
          />
          <IconButton
            :icon="TableProperties"
            :label="t('document.documentsPage.tableView')"
            size="sm"
            :variant="documentStore.viewMode === 'table' ? 'primary' : 'ghost'"
            @click="documentStore.setViewMode('table')"
          />
        </div>
      </template>
    </FilterBar>

    <ErrorState v-if="documentStore.error" :description="documentStore.error" @retry="loadData" />

    <template v-else-if="documentStore.viewMode === 'grid'">
      <div v-if="documentStore.isPageLoading" class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
        <div v-for="placeholder in 6" :key="placeholder" class="rounded-xl border border-border-light bg-bg-card p-5">
          <SkeletonLoader :rows="5" />
        </div>
      </div>

      <EmptyState
        v-else-if="documentStore.pageItems.length === 0"
        :title="t('document.documentsPage.noDocumentsFound')"
        :description="t('document.documentsPage.noDocumentsFoundDescription')"
        :action-label="t('document.documentsPage.uploadDocument')"
        @action="isUploadDialogOpen = true"
      />

      <template v-else>
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
          <DocumentCard
            v-for="document in documentStore.pageItems"
            :key="document.id"
            :document="document"
            :project="documentStore.getProjectById(document.projectId)"
            @open="openDocument"
          />
        </div>
        <div class="rounded-xl border border-border-light bg-bg-card">
          <TablePagination
            :current-page="documentStore.pagination.page"
            :total-pages="documentStore.pagination.totalPages"
            :total-items="documentStore.pagination.total"
            :start-index="(documentStore.pagination.page - 1) * documentStore.pagination.pageSize"
            :end-index="Math.min(documentStore.pagination.page * documentStore.pagination.pageSize, documentStore.pagination.total)"
            :page-size="documentStore.pagination.pageSize"
            :page-size-options="[9, 18, 27]"
            @page-change="documentStore.setPage"
            @page-size-change="documentStore.setPageSize"
          />
        </div>
      </template>
    </template>

    <template v-else>
      <SmartTable
        :columns="TABLE_COLUMNS"
        :rows="tableRows"
        row-key="id"
        :loading="documentStore.isPageLoading"
        :searchable="false"
        :paginated="false"
        :empty-title="t('document.documentsPage.noDocumentsFound')"
        :empty-description="t('document.documentsPage.noDocumentsFoundDescription')"
        @row-click="openDocument($event.id)"
      >
        <template #cell-type="{ value }">
          <StatusBadge :label="typeLabel(value as string)" variant="info" />
        </template>
        <template #cell-status="{ value }">
          <StatusBadge :label="statusLabel(value as string)" :variant="getDocumentStatusVariant(value as DocumentStatus)" show-dot />
        </template>
        <template #cell-uploadDate="{ value }">
          {{ formatDate(value as string) }}
        </template>
      </SmartTable>
      <div class="rounded-xl border border-border-light bg-bg-card">
        <TablePagination
          :current-page="documentStore.pagination.page"
          :total-pages="documentStore.pagination.totalPages"
          :total-items="documentStore.pagination.total"
          :start-index="(documentStore.pagination.page - 1) * documentStore.pagination.pageSize"
          :end-index="Math.min(documentStore.pagination.page * documentStore.pagination.pageSize, documentStore.pagination.total)"
          :page-size="documentStore.pagination.pageSize"
          :page-size-options="[10, 25, 50]"
          @page-change="documentStore.setPage"
          @page-size-change="documentStore.setPageSize"
        />
      </div>
    </template>

    <DocumentUploadDialog v-model="isUploadDialogOpen" :projects="documentStore.projects" @upload="handleUpload" />
  </div>
</template>
