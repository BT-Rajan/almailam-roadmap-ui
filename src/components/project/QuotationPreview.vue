<script setup lang="ts">
import { FileText } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import Divider from '@/components/common/Divider.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import EditableLineItems from '@/components/project/EditableLineItems.vue'
import PricingSummary from '@/components/project/PricingSummary.vue'
import QuotationLetterDesignPermits from '@/components/project/letters/QuotationLetterDesignPermits.vue'
import QuotationLetterSupervision from '@/components/project/letters/QuotationLetterSupervision.vue'
import EditableList from '@/components/project/letters/EditableList.vue'
import EditableText from '@/components/project/letters/EditableText.vue'
import { formatDate } from '@/utils/dateFormatter'
import { getQuotationStatusVariant } from '@/utils/quotationHelpers'
import type { Client } from '@/types/Client'
import type { Project } from '@/types/Project'
import type { Quotation, QuotationLineItem } from '@/types/Quotation'

interface Props {
  quotation: Quotation
  project: Project
  client?: Client
}

withDefaults(defineProps<Props>(), {
  client: undefined,
})

const emit = defineEmits<{ patch: [value: Partial<Quotation>] }>()

const LETTER_COMPONENTS = {
  'design-and-permits': QuotationLetterDesignPermits,
  supervision: QuotationLetterSupervision,
} as const

function updateLineItems(items: QuotationLineItem[]): void {
  emit('patch', { lineItems: items })
}

function updateNotes(value: string): void {
  emit('patch', { notes: value })
}

function updateTerms(value: string[]): void {
  emit('patch', { termsAndConditions: value })
}
</script>

<template>
  <Card class="print:shadow-none" :padded="true">
    <div id="quotation-print-area" class="flex flex-col gap-6">
      <template v-if="quotation.templateKey">
        <div class="no-print flex items-center justify-between">
          <div class="flex items-center gap-2">
            <h2 class="text-lg font-semibold text-text-primary">{{ quotation.quotationNo }}</h2>
            <StatusBadge :label="quotation.status" :variant="getQuotationStatusVariant(quotation.status)" />
          </div>
          <span
            class="rounded-full px-2.5 py-1 text-xs font-medium"
            :class="quotation.finalizedAt ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'"
          >
            {{ quotation.finalizedAt ? 'Final' : 'Draft — click text to edit' }}
          </span>
        </div>
        <component
          :is="LETTER_COMPONENTS[quotation.templateKey]"
          :quotation="quotation"
          :editable="!quotation.finalizedAt"
          @patch="(v) => emit('patch', v)"
        />
      </template>

      <template v-else>
      <div class="no-print flex justify-end">
        <span
          class="rounded-full px-2.5 py-1 text-xs font-medium"
          :class="quotation.finalizedAt ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'"
        >
          {{ quotation.finalizedAt ? 'Final' : 'Draft — click text to edit' }}
        </span>
      </div>
      <div class="flex flex-col gap-4 tablet:flex-row tablet:items-start tablet:justify-between">
        <div class="flex items-center gap-3">
          <span class="flex h-11 w-11 items-center justify-center rounded-lg bg-primary-50 text-primary-700">
            <FileText class="h-5 w-5" />
          </span>
          <div>
            <p class="text-sm font-semibold text-text-primary">Almailam Engineering Consultants</p>
            <p class="text-xs text-text-muted">Engineering Design & Government Approvals</p>
          </div>
        </div>

        <div class="flex flex-col gap-1 tablet:items-end">
          <div class="flex items-center gap-2">
            <h2 class="text-lg font-semibold text-text-primary">{{ quotation.quotationNo }}</h2>
            <StatusBadge :label="quotation.status" :variant="getQuotationStatusVariant(quotation.status)" />
          </div>
          <p class="text-xs text-text-muted">Revision {{ quotation.revision }}</p>
        </div>
      </div>

      <Divider />

      <div class="grid grid-cols-1 gap-6 tablet:grid-cols-3">
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Bill To</p>
          <p class="text-sm font-semibold text-text-primary">{{ client?.companyName ?? 'Unknown Client' }}</p>
          <p class="text-sm text-text-muted">{{ client?.contactPerson }}</p>
          <p class="text-sm text-text-muted">{{ client?.city }}</p>
        </div>
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Project</p>
          <p class="text-sm font-semibold text-text-primary">{{ project.projectName }}</p>
          <p class="text-sm text-text-muted">{{ project.projectNo }} · {{ project.service }}</p>
        </div>
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Dates</p>
          <p class="text-sm text-text-muted">Issued: {{ formatDate(quotation.issueDate) }}</p>
          <p class="text-sm text-text-muted">Valid Until: {{ formatDate(quotation.validity) }}</p>
          <p class="text-sm text-text-muted">Prepared By: {{ quotation.preparedBy }}</p>
        </div>
      </div>

      <Divider />

      <EditableLineItems
        :model-value="quotation.lineItems"
        :editable="!quotation.finalizedAt"
        :currency="quotation.currency"
        @update:model-value="updateLineItems"
      />

      <div class="flex justify-end">
        <div class="w-full tablet:w-80">
          <PricingSummary :quotation="quotation" />
        </div>
      </div>

      <div v-if="quotation.notes || !quotation.finalizedAt" class="flex flex-col gap-1">
        <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Notes</p>
        <EditableText
          :model-value="quotation.notes"
          :editable="!quotation.finalizedAt"
          multiline
          placeholder="Optional notes for this quotation"
          class="text-sm text-text-secondary"
          @update:model-value="updateNotes"
        />
      </div>

      <div class="flex flex-col gap-2">
        <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Terms & Conditions</p>
        <EditableList
          :model-value="quotation.termsAndConditions"
          :editable="!quotation.finalizedAt"
          @update:model-value="updateTerms"
        />
      </div>
      </template>
    </div>
  </Card>
</template>

