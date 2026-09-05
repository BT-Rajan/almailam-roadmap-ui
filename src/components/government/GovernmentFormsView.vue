<script setup lang="ts">
import { Pencil, Trash2 } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import GovernmentFormCard from '@/components/government/GovernmentFormCard.vue'
import type { GovernmentAuthority, GovernmentForm, GovernmentFormCategory } from '@/types/Government'
import type { SmartTableColumn } from '@/types/Table'
import { formatDate } from '@/utils/dateFormatter'
import { getFormCategoryVariant } from '@/utils/governmentFormHelpers'

interface GovernmentFormTableRow {
  [key: string]: unknown
  id: string
  formCode: string
  title: string
  category: GovernmentFormCategory
  language: string
  version: string
  lastUpdated: string
  status: string
}

const props = defineProps<{
  forms: GovernmentForm[]
  authority: GovernmentAuthority
  viewMode: 'grid' | 'table'
}>()

const emit = defineEmits<{
  view: [form: GovernmentForm]
  aiHelp: [form: GovernmentForm]
  edit: [form: GovernmentForm]
  archive: [form: GovernmentForm]
  restore: [form: GovernmentForm]
  addForm: []
}>()

const { t } = useI18n()

const TABLE_COLUMNS = computed<SmartTableColumn<GovernmentFormTableRow>[]>(() => [
  { key: 'formCode', label: t('government.formsView.columnFormCode'), sortable: true, width: '130px' },
  { key: 'title', label: t('government.formsView.columnFormTitle'), sortable: true },
  { key: 'category', label: t('government.formsView.columnCategory'), sortable: true },
  { key: 'language', label: t('government.formsView.columnLanguage'), sortable: true },
  { key: 'version', label: t('government.formsView.columnVersion'), sortable: true, width: '100px' },
  { key: 'status', label: t('government.formsView.columnStatus'), sortable: true, width: '100px' },
  { key: 'lastUpdated', label: t('government.formsView.columnLastUpdated'), sortable: true, align: 'right' },
])

const tableRows = computed<GovernmentFormTableRow[]>(() =>
  props.forms.map((form) => ({
    id: form.id,
    formCode: form.formCode,
    title: form.title,
    category: form.category,
    language: form.language,
    version: form.version,
    status: form.status,
    lastUpdated: form.lastUpdated,
  })),
)

function formById(formId: string): GovernmentForm | undefined {
  return props.forms.find((form) => form.id === formId)
}

function statusLabel(status: string): string {
  return status === 'Archived' ? t('government.formStatus.archived') : t('government.formStatus.active')
}
</script>

<template>
  <template v-if="viewMode === 'grid'">
    <EmptyState
      v-if="forms.length === 0"
      :title="t('government.formsView.noFormsFound')"
      :description="t('government.formsView.noFormsFoundDescription')"
      :action-label="t('government.formLibraryPanel.addForm')"
      @action="emit('addForm')"
    />
    <div v-else class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
      <GovernmentFormCard
        v-for="form in forms"
        :key="form.id"
        :form="form"
        :authority="authority"
        @view="emit('view', form)"
        @ai-help="emit('aiHelp', form)"
        @edit="emit('edit', form)"
        @archive="emit('archive', form)"
        @restore="emit('restore', form)"
      />
    </div>
  </template>

  <SmartTable
    v-else
    :columns="TABLE_COLUMNS"
    :rows="tableRows"
    row-key="id"
    :searchable="false"
    :empty-title="t('government.formsView.noFormsFound')"
    :empty-description="t('government.formsView.noFormsFoundDescription')"
    @row-click="(row) => formById(row.id) && emit('view', formById(row.id)!)"
  >
    <template #cell-category="{ value }">
      <StatusBadge :label="value as string" :variant="getFormCategoryVariant(value as GovernmentFormCategory)" />
    </template>
    <template #cell-status="{ value }">
      <StatusBadge :label="statusLabel(value as string)" :variant="value === 'Archived' ? 'neutral' : 'success'" />
    </template>
    <template #cell-lastUpdated="{ value }">
      {{ formatDate(value as string) }}
    </template>
    <template #row-actions="{ row }">
      <div class="flex items-center justify-end gap-1" @click.stop>
        <IconButton
          :icon="Pencil"
          :label="t('government.formsView.editForm')"
          size="sm"
          variant="ghost"
          @click="formById(row.id) && emit('edit', formById(row.id)!)"
        />
        <IconButton
          :icon="Trash2"
          :label="t('government.formsView.archiveForm')"
          size="sm"
          variant="ghost"
          @click="formById(row.id) && emit('archive', formById(row.id)!)"
        />
      </div>
    </template>
  </SmartTable>
</template>
