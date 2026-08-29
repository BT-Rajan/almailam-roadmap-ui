<script setup lang="ts">
import { Check, FileText, Pencil, Plus, Trash2, X } from '@lucide/vue'
import { reactive, ref, watch } from 'vue'

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
import PricingSummary from '@/components/project/PricingSummary.vue'
import type { Client } from '@/types/Client'
import type { Project } from '@/types/Project'
import type { Quotation } from '@/types/Quotation'
import type { SelectOption } from '@/types/Ui'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { getQuotationStatusVariant } from '@/utils/quotationHelpers'
import { sanitizeHtml } from '@/utils/sanitizeHtml'

interface Props {
  quotation: Quotation
  project: Project
  client?: Client
}

const props = withDefaults(defineProps<Props>(), {
  client: undefined,
})

const emit = defineEmits<{
  patch: [value: Partial<Quotation>]
  saveAsFinal: [value: Partial<Quotation>]
}>()

const CURRENCY_OPTIONS: SelectOption[] = [
  { label: 'KWD', value: 'KWD' },
  { label: 'USD', value: 'USD' },
  { label: 'AED', value: 'AED' },
  { label: 'EUR', value: 'EUR' },
]

// Click Edit to unlock changes, Save/Save as Final to lock them back down.
const isEditing = ref(false)

interface DraftLineItem {
  id: string
  description: string
  quantity: number
  unitPrice: number
}

function draftFromQuotation(quotation: Quotation) {
  return {
    validity: quotation.validity,
    currency: quotation.currency,
    discountAmount: quotation.discountAmount,
    notes: quotation.notes,
    terms: [...quotation.termsAndConditions],
    lineItems: quotation.lineItems.map((item) => ({ ...item })) as DraftLineItem[],
  }
}

// A term editor can be left visually empty (just "<p><br></p>" etc) --
// strip tags before checking so those don't get saved as empty terms.
function isBlankHtml(html: string): boolean {
  return html.replace(/<[^>]*>/g, '').trim().length === 0
}

const draft = reactive(draftFromQuotation(props.quotation))

// Switching to a different quotation (or the store refreshing this one
// after finalize/reopen) always drops out of edit mode rather than
// silently continuing to edit against what's now stale data.
watch(
  () => props.quotation.id,
  () => {
    isEditing.value = false
  },
)

function startEditing(): void {
  Object.assign(draft, draftFromQuotation(props.quotation))
  isEditing.value = true
}

function cancelEditing(): void {
  isEditing.value = false
}

function addLineItem(): void {
  draft.lineItems.push({ id: `new-${draft.lineItems.length}-${Date.now()}`, description: '', quantity: 1, unitPrice: 0 })
}

function removeLineItem(index: number): void {
  if (draft.lineItems.length === 1) return
  draft.lineItems.splice(index, 1)
}

function addTerm(): void {
  draft.terms.push('')
}

function removeTerm(index: number): void {
  draft.terms.splice(index, 1)
}

function buildPatch(): Partial<Quotation> {
  return {
    validity: draft.validity,
    currency: draft.currency,
    discountAmount: draft.discountAmount,
    notes: draft.notes,
    termsAndConditions: draft.terms.filter((term) => !isBlankHtml(term)),
    lineItems: draft.lineItems.map((item) => ({
      id: item.id,
      description: item.description.trim(),
      quantity: item.quantity,
      unitPrice: item.unitPrice,
    })),
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
</script>

<template>
  <Card class="print:shadow-none" :padded="true">
    <div id="quotation-print-area" class="flex flex-col gap-6">
      <div class="no-print flex items-center justify-between">
        <div class="flex items-center gap-2">
          <h2 class="text-lg font-semibold text-text-primary">{{ quotation.quotationNo }}</h2>
          <StatusBadge :label="quotation.status" :variant="getQuotationStatusVariant(quotation.status)" />
        </div>
        <div class="flex items-center gap-2">
          <span
            class="rounded-full px-2.5 py-1 text-xs font-medium"
            :class="quotation.finalizedAt ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'"
          >
            {{ quotation.finalizedAt ? 'Content Locked' : isEditing ? 'Editing' : 'Editable' }}
          </span>
          <BaseButton v-if="!quotation.finalizedAt && !isEditing" variant="secondary" size="sm" :icon="Pencil" @click="startEditing">
            Edit
          </BaseButton>
          <template v-else-if="isEditing">
            <BaseButton variant="ghost" size="sm" :icon="X" @click="cancelEditing">Cancel</BaseButton>
            <BaseButton variant="secondary" size="sm" :icon="Check" @click="saveDraft">Save</BaseButton>
            <BaseButton size="sm" @click="saveAsFinal">Save as Final</BaseButton>
          </template>
        </div>
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
          <template v-if="isEditing">
            <DatePicker v-model="draft.validity" label="Valid Until" />
            <SelectBox v-model="draft.currency" label="Currency" :options="CURRENCY_OPTIONS" />
          </template>
          <p v-else class="text-sm text-text-muted">Valid Until: {{ formatDate(quotation.validity) }}</p>
          <p class="text-sm text-text-muted">Prepared By: {{ quotation.preparedBy }}</p>
        </div>
      </div>

      <Divider />

      <div v-if="!isEditing" class="overflow-x-auto">
        <table class="w-full border-collapse">
          <thead>
            <tr class="border-b border-border-light bg-bg-secondary">
              <th class="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-text-muted">
                Description
              </th>
              <th class="px-3 py-2.5 text-right text-xs font-semibold uppercase tracking-wide text-text-muted">
                Qty
              </th>
              <th class="px-3 py-2.5 text-right text-xs font-semibold uppercase tracking-wide text-text-muted">
                Unit Price
              </th>
              <th class="px-3 py-2.5 text-right text-xs font-semibold uppercase tracking-wide text-text-muted">
                Amount
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in quotation.lineItems" :key="item.id" class="border-b border-border-light last:border-0">
              <td class="px-3 py-3 text-sm text-text-secondary">{{ item.description }}</td>
              <td class="px-3 py-3 text-right text-sm text-text-secondary">{{ item.quantity }}</td>
              <td class="px-3 py-3 text-right text-sm text-text-secondary">
                {{ formatCurrency(item.unitPrice, quotation.currency) }}
              </td>
              <td class="px-3 py-3 text-right text-sm font-medium text-text-primary">
                {{ formatCurrency(item.quantity * item.unitPrice, quotation.currency) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <label class="text-sm font-medium text-text-secondary">Line Items</label>
          <BaseButton variant="ghost" size="sm" :icon="Plus" @click="addLineItem">Add Line Item</BaseButton>
        </div>
        <div v-for="(item, index) in draft.lineItems" :key="item.id" class="flex flex-col gap-2 rounded-lg border border-border-light p-3">
          <div class="flex items-start gap-2">
            <div class="flex-1">
              <TextInput v-model="item.description" placeholder="Description" />
            </div>
            <IconButton :icon="Trash2" :label="`Remove line item ${index + 1}`" size="sm" :disabled="draft.lineItems.length === 1" @click="removeLineItem(index)" />
          </div>
          <div class="grid grid-cols-2 gap-2">
            <NumberInput :model-value="item.quantity" placeholder="Quantity" :min="0.01" step="0.01" @update:model-value="item.quantity = Number($event)" />
            <NumberInput :model-value="item.unitPrice" placeholder="Unit Price" :min="0" step="0.01" @update:model-value="item.unitPrice = Number($event)" />
          </div>
        </div>
      </div>

      <div v-if="isEditing" class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <NumberInput
          :model-value="draft.discountAmount"
          label="Discount Amount"
          :min="0"
          step="0.01"
          @update:model-value="draft.discountAmount = Number($event)"
        />
      </div>

      <div class="flex justify-end">
        <div class="w-full tablet:w-80">
          <PricingSummary :quotation="isEditing ? { ...quotation, ...buildPatch() } : quotation" />
        </div>
      </div>

      <div v-if="isEditing" class="flex flex-col gap-1.5">
        <RichTextEditor v-model="draft.notes" label="Notes" placeholder="Optional notes for this quotation" />
      </div>
      <div v-else-if="quotation.notes" class="flex flex-col gap-1">
        <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Notes</p>
        <div class="rich-text-content text-sm text-text-secondary" v-html="sanitizeHtml(quotation.notes)" />
      </div>

      <div v-if="isEditing" class="flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <label class="text-sm font-medium text-text-secondary">Terms &amp; Conditions</label>
          <BaseButton variant="ghost" size="sm" :icon="Plus" @click="addTerm">Add Term</BaseButton>
        </div>
        <div v-for="(term, index) in draft.terms" :key="index" class="flex items-start gap-2">
          <div class="flex-1">
            <RichTextEditor :model-value="term" @update:model-value="draft.terms[index] = $event" />
          </div>
          <IconButton :icon="Trash2" :label="`Remove term ${index + 1}`" size="sm" @click="removeTerm(index)" />
        </div>
      </div>
      <div v-else-if="quotation.termsAndConditions.length" class="flex flex-col gap-2">
        <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Terms & Conditions</p>
        <ul class="flex flex-col gap-1">
          <li
            v-for="(term, index) in quotation.termsAndConditions"
            :key="index"
            class="flex gap-2 text-sm text-text-muted"
          >
            <span class="text-text-muted">•</span>
            <div class="rich-text-content flex-1" v-html="sanitizeHtml(term)" />
          </li>
        </ul>
      </div>
    </div>
  </Card>
</template>
