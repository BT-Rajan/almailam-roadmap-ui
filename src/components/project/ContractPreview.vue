<script setup lang="ts">
import { Check, FileSignature, Pencil, X } from '@lucide/vue'
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import Divider from '@/components/common/Divider.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { Client } from '@/types/Client'
import type { Contract } from '@/types/Contract'
import type { Project } from '@/types/Project'
import { getClientFormalName } from '@/utils/clientHelpers'
import { getContractStatusVariant, getDesignPermitPeriod, getSupervisionPeriod } from '@/utils/contractHelpers'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
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
}>()

const { t } = useI18n()

// Filled in automatically from the project, never edited on the
// contract itself -- same as the New Contract page.
const designPermitPeriod = computed(() => getDesignPermitPeriod(props.project))
const supervisionPeriod = computed(() => getSupervisionPeriod(props.project))

function displayDate(value: string | null | undefined): string {
  return value ? formatDate(value) : '—'
}

// Same edit-mode flow as QuotationPreview -- click Edit to unlock
// changes, Save to persist them as a new draft revision. Finalizing
// (locking content) only happens via the toolbar's Decision actions,
// same as QuotationPreview -- there's no separate "Save as Final" here.
const isEditing = ref(false)

function draftFromContract(contract: Contract) {
  return {
    contractValue: contract.contractValue,
    expiryDate: contract.expiryDate,
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

function buildPatch(): Partial<Contract> {
  // Currency and Scope Summary are locked once a contract exists (they
  // carry over from the source quotation), so neither is part of an edit.
  return {
    contractValue: draft.contractValue,
    expiryDate: draft.expiryDate,
    // Clauses aren't authored any more (the contract document is the cost
    // workout); leaving them out of the patch keeps any existing ones.
  }
}

function saveDraft(): void {
  emit('patch', buildPatch())
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
            <BaseButton size="sm" :icon="Check" @click="saveDraft">{{ t('common.save') }}</BaseButton>
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
          <p class="text-sm font-semibold text-text-primary">{{ client ? getClientFormalName(client) : t('client.unknownClient') }}</p>
        </div>
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.quotationPreview.project') }}</p>
          <p class="text-sm font-semibold text-text-primary">{{ project.projectName }} ({{ project.projectNo }})</p>
          <p class="text-sm text-text-muted">{{ project.service }}</p>
        </div>
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.quotationPreview.dates') }}</p>
          <p class="text-sm text-text-muted">{{ t('project.quotationPreview.issued', { date: formatDate(contract.issueDate) }) }}</p>
          <p v-if="contract.signedDate" class="text-sm text-text-muted">
            {{ t('project.contractPreview.signed', { date: formatDate(contract.signedDate) }) }}
          </p>
          <DatePicker v-if="isEditing" v-model="draft.expiryDate" :label="t('project.contractPreview.expiryDate')" />
          <p v-else class="text-sm text-text-muted">{{ t('project.contractPreview.expires', { date: formatDate(contract.expiryDate) }) }}</p>
        </div>
      </div>

      <div v-if="designPermitPeriod || supervisionPeriod" class="grid grid-cols-1 gap-6 tablet:grid-cols-2">
        <template v-if="designPermitPeriod">
          <div class="flex flex-col gap-1">
            <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.contractDates.designPermitStart') }}</p>
            <p class="text-sm text-text-primary">{{ displayDate(designPermitPeriod.start) }}</p>
          </div>
          <div class="flex flex-col gap-1">
            <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.contractDates.designPermitEnd') }}</p>
            <p class="text-sm text-text-primary">{{ displayDate(designPermitPeriod.end) }}</p>
          </div>
        </template>
        <template v-if="supervisionPeriod">
          <div class="flex flex-col gap-1">
            <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.contractDates.supervisionStart') }}</p>
            <p class="text-sm text-text-primary">{{ displayDate(supervisionPeriod.start) }}</p>
          </div>
          <div class="flex flex-col gap-1">
            <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.contractDates.supervisionEnd') }}</p>
            <p class="text-sm text-text-primary">{{ displayDate(supervisionPeriod.end) }}</p>
          </div>
        </template>
      </div>

      <Divider />

      <div class="flex flex-col gap-2">
        <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.contractPreview.scopeSummary') }}</p>
        <div class="rich-text-content text-sm text-text-secondary" v-html="sanitizeHtml(contract.scopeSummary)" />
      </div>

      <div class="flex items-center justify-between rounded-lg bg-bg-secondary px-4 py-3">
        <span class="text-sm font-medium text-text-secondary">{{ t('project.contractPreview.contractValue') }}</span>
        <NumberInput
          v-if="isEditing"
          :model-value="draft.contractValue"
          :prefix="contract.currency"
          :min="0.01"
          step="0.01"
          class="w-56"
          @update:model-value="draft.contractValue = Number($event)"
        />
        <span v-else class="text-lg font-semibold text-primary-700">
          {{ formatCurrency(contract.contractValue, contract.currency) }}
        </span>
      </div>

      <!-- Read-only: only contracts created before clause framing was
           removed have any. -->
      <div v-if="contract.clauses.length > 0" class="flex flex-col gap-4">
        <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.contractPreview.clauses') }}</p>
        <div
          v-for="(clause, index) in contract.clauses"
          :key="clause.id"
          class="flex flex-col gap-1 border-b border-border-light pb-4 last:border-0 last:pb-0"
        >
          <p class="text-sm font-semibold text-text-primary">{{ index + 1 }}. {{ clause.title }}</p>
          <div class="rich-text-content text-sm text-text-secondary" v-html="sanitizeHtml(clause.content)" />
        </div>
      </div>

      <p class="no-print text-center text-xs text-text-muted">
        {{ t('project.contractPreview.prototypeNotice') }}
      </p>
    </div>
  </Card>
</template>
