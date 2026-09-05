<script setup lang="ts">
import { Check, FileSignature, Pencil, Plus, Trash2, X } from '@lucide/vue'
import { reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import Divider from '@/components/common/Divider.vue'
import IconButton from '@/components/common/IconButton.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import RichTextEditor from '@/components/common/RichTextEditor.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextInput from '@/components/common/TextInput.vue'
import type { Client } from '@/types/Client'
import type { Contract, ContractClause } from '@/types/Contract'
import type { Project } from '@/types/Project'
import type { SelectOption } from '@/types/Ui'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { getContractStatusVariant } from '@/utils/contractHelpers'
import { sanitizeHtml } from '@/utils/sanitizeHtml'

interface Props {
  contract: Contract
  project: Project
  client?: Client
}

const props = withDefaults(defineProps<Props>(), {
  client: undefined,
})

const emit = defineEmits<{
  patch: [value: Partial<Contract>]
  saveAsFinal: [value: Partial<Contract>]
}>()

const { t } = useI18n()

const CURRENCY_OPTIONS: SelectOption[] = [
  { label: 'KWD', value: 'KWD' },
  { label: 'USD', value: 'USD' },
  { label: 'EUR', value: 'EUR' },
]

// Same edit-mode flow as QuotationPreview -- click Edit to unlock changes,
// Save/Save as Final to lock them back down.
const isEditing = ref(false)

interface DraftClause {
  id: string
  title: string
  content: string
}

function draftFromContract(contract: Contract) {
  return {
    currency: contract.currency,
    contractValue: contract.contractValue,
    expiryDate: contract.expiryDate,
    clientRepresentative: contract.clientRepresentative,
    scopeSummary: contract.scopeSummary,
    clauses: contract.clauses.map((clause) => ({ ...clause })) as DraftClause[],
  }
}

const draft = reactive(draftFromContract(props.contract))

// Switching to a different contract (or the store refreshing this one
// after finalize/reopen) always drops out of edit mode rather than
// silently continuing to edit against what's now stale data.
watch(
  () => props.contract.id,
  () => {
    isEditing.value = false
  },
)

function startEditing(): void {
  Object.assign(draft, draftFromContract(props.contract))
  isEditing.value = true
}

function cancelEditing(): void {
  isEditing.value = false
}

function addClause(): void {
  draft.clauses.push({ id: `new-${draft.clauses.length}-${Date.now()}`, title: '', content: '' })
}

function removeClause(index: number): void {
  draft.clauses.splice(index, 1)
}

function buildPatch(): Partial<Contract> {
  return {
    currency: draft.currency,
    contractValue: draft.contractValue,
    expiryDate: draft.expiryDate,
    clientRepresentative: draft.clientRepresentative.trim(),
    scopeSummary: draft.scopeSummary.trim(),
    clauses: draft.clauses.map((clause) => ({
      id: clause.id,
      title: clause.title.trim(),
      content: clause.content.trim(),
    })) as ContractClause[],
  }
}

function saveDraft(): void {
  emit('patch', buildPatch())
  isEditing.value = false
}

function saveAsFinal(): void {
  emit('saveAsFinal', buildPatch())
  isEditing.value = false
}

const CONTRACT_STATUS_KEYS: Record<Contract['status'], string> = {
  Draft: 'project.contractStatus.draft',
  Signed: 'project.contractStatus.signed',
  Active: 'project.contractStatus.active',
  Expired: 'project.contractStatus.expired',
  Terminated: 'project.contractStatus.terminated',
}
</script>

<template>
  <Card class="print:shadow-none" :padded="true">
    <div id="contract-print-area" class="flex flex-col gap-6">
      <div class="no-print flex items-center justify-between">
        <div class="flex items-center gap-2">
          <h2 class="text-lg font-semibold text-text-primary">{{ contract.contractNo }}</h2>
          <StatusBadge :label="t(CONTRACT_STATUS_KEYS[contract.status])" :variant="getContractStatusVariant(contract.status)" />
        </div>
        <div class="flex items-center gap-2">
          <span
            class="rounded-full px-2.5 py-1 text-xs font-medium"
            :class="contract.finalizedAt ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'"
          >
            {{ contract.finalizedAt ? t('project.quotationPreview.contentLocked') : isEditing ? t('project.quotationPreview.editing') : t('project.quotationPreview.editable') }}
          </span>
          <BaseButton v-if="!contract.finalizedAt && !isEditing" variant="secondary" size="sm" :icon="Pencil" @click="startEditing">
            {{ t('common.edit') }}
          </BaseButton>
          <template v-else-if="isEditing">
            <BaseButton variant="ghost" size="sm" :icon="X" @click="cancelEditing">{{ t('common.cancel') }}</BaseButton>
            <BaseButton variant="secondary" size="sm" :icon="Check" @click="saveDraft">{{ t('common.save') }}</BaseButton>
            <BaseButton size="sm" @click="saveAsFinal">{{ t('project.quotationPreview.saveAsFinal') }}</BaseButton>
          </template>
        </div>
      </div>

      <div class="flex flex-col gap-4 tablet:flex-row tablet:items-start tablet:justify-between">
        <div class="flex items-center gap-3">
          <span class="flex h-11 w-11 items-center justify-center rounded-lg bg-primary-50 text-primary-700">
            <FileSignature class="h-5 w-5" />
          </span>
          <div>
            <p class="text-sm font-semibold text-text-primary">{{ t('common.companyName') }}</p>
            <p class="text-xs text-text-muted">{{ t('project.quotationPreview.companyTagline') }}</p>
          </div>
        </div>

        <div class="flex flex-col gap-1 tablet:items-end">
          <p class="text-xs text-text-muted">{{ t('project.quotationPreview.revision', { revision: contract.revision }) }}</p>
        </div>
      </div>

      <Divider />

      <div class="grid grid-cols-1 gap-6 tablet:grid-cols-3">
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.contractPreview.client') }}</p>
          <p class="text-sm font-semibold text-text-primary">{{ client?.companyName ?? t('client.unknownClient') }}</p>
          <TextInput v-if="isEditing" v-model="draft.clientRepresentative" :placeholder="t('project.contractPreview.clientRepresentative')" class="mt-1" />
          <p v-else class="text-sm text-text-muted">{{ t('project.contractPreview.representedBy', { name: contract.clientRepresentative }) }}</p>
        </div>
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.quotationPreview.project') }}</p>
          <p class="text-sm font-semibold text-text-primary">{{ project.projectName }}</p>
          <p class="text-sm text-text-muted">{{ project.projectNo }} · {{ project.service }}</p>
        </div>
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.quotationPreview.dates') }}</p>
          <p class="text-sm text-text-muted">{{ t('project.quotationPreview.issued', { date: formatDate(contract.issueDate) }) }}</p>
          <p v-if="contract.signedDate" class="text-sm text-text-muted">
            {{ t('project.contractPreview.signed', { date: formatDate(contract.signedDate) }) }}
          </p>
          <template v-if="isEditing">
            <DatePicker v-model="draft.expiryDate" :label="t('project.contractPreview.expiryDate')" />
            <SelectBox v-model="draft.currency" :label="t('project.quotationPreview.currency')" :options="CURRENCY_OPTIONS" />
          </template>
          <p v-else class="text-sm text-text-muted">{{ t('project.contractPreview.expires', { date: formatDate(contract.expiryDate) }) }}</p>
        </div>
      </div>

      <Divider />

      <div class="flex flex-col gap-2">
        <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.contractPreview.scopeSummary') }}</p>
        <RichTextEditor v-if="isEditing" v-model="draft.scopeSummary" />
        <div v-else class="rich-text-content text-sm text-text-secondary" v-html="sanitizeHtml(contract.scopeSummary)" />
      </div>

      <div class="flex items-center justify-between rounded-lg bg-bg-secondary px-4 py-3">
        <span class="text-sm font-medium text-text-secondary">{{ t('project.contractPreview.contractValue') }}</span>
        <NumberInput
          v-if="isEditing"
          :model-value="draft.contractValue"
          :min="0.01"
          step="0.01"
          class="w-40"
          @update:model-value="draft.contractValue = Number($event)"
        />
        <span v-else class="text-lg font-semibold text-primary-700">
          {{ formatCurrency(contract.contractValue, contract.currency) }}
        </span>
      </div>

      <div class="flex flex-col gap-4">
        <div class="flex items-center justify-between">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.contractPreview.clauses') }}</p>
          <BaseButton v-if="isEditing" variant="ghost" size="sm" :icon="Plus" @click="addClause">{{ t('project.contractPreview.addClause') }}</BaseButton>
        </div>

        <template v-if="!isEditing">
          <div
            v-for="(clause, index) in contract.clauses"
            :key="clause.id"
            class="flex flex-col gap-1 border-b border-border-light pb-4 last:border-0 last:pb-0"
          >
            <p class="text-sm font-semibold text-text-primary">{{ index + 1 }}. {{ clause.title }}</p>
            <div class="rich-text-content text-sm text-text-secondary" v-html="sanitizeHtml(clause.content)" />
          </div>
        </template>
        <template v-else>
          <div v-for="(clause, index) in draft.clauses" :key="clause.id" class="flex flex-col gap-2 rounded-lg border border-border-light p-3">
            <div class="flex items-start gap-2">
              <div class="flex-1">
                <TextInput v-model="clause.title" :placeholder="t('project.contractPreview.clauseTitle')" />
              </div>
              <IconButton :icon="Trash2" :label="t('project.contractPreview.removeClause', { index: index + 1 })" size="sm" @click="removeClause(index)" />
            </div>
            <RichTextEditor v-model="clause.content" :placeholder="t('project.contractPreview.clauseContent')" />
          </div>
        </template>
      </div>

      <p class="no-print text-center text-xs text-text-muted">
        {{ t('project.contractPreview.prototypeNotice') }}
      </p>
    </div>
  </Card>
</template>
