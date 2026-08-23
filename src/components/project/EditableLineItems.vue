<script setup lang="ts">
/**
 * The itemised quotation's line-items table -- description, quantity,
 * unit price per row. Same "RTF" contenteditable pattern as
 * EditableText/EditableList (see those for the print/read-view rationale),
 * just three cells per row instead of one field, plus add/remove-row
 * controls. Quantity/unit price are parsed back to numbers on blur;
 * an unparseable edit (stray letters, empty) silently reverts to the
 * row's last valid value rather than saving garbage or NaN.
 */
import { Plus, Trash2 } from '@lucide/vue'

import EditableText from '@/components/project/letters/EditableText.vue'
import type { QuotationLineItem } from '@/types/Quotation'
import { formatCurrency } from '@/utils/currencyFormatter'

const props = defineProps<{
  modelValue: QuotationLineItem[]
  editable: boolean
  currency: string
}>()

const emit = defineEmits<{ 'update:modelValue': [value: QuotationLineItem[]] }>()

function parseNumber(raw: string, fallback: number): number {
  const parsed = Number(raw.replace(/,/g, '').trim())
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : fallback
}

function updateDescription(index: number, value: string): void {
  const next = props.modelValue.map((item, i) => (i === index ? { ...item, description: value } : item))
  emit('update:modelValue', next)
}

function updateQuantity(index: number, raw: string): void {
  const next = props.modelValue.map((item, i) =>
    i === index ? { ...item, quantity: parseNumber(raw, item.quantity) } : item,
  )
  emit('update:modelValue', next)
}

function updateUnitPrice(index: number, raw: string): void {
  const next = props.modelValue.map((item, i) =>
    i === index ? { ...item, unitPrice: parseNumber(raw, item.unitPrice) } : item,
  )
  emit('update:modelValue', next)
}

function removeRow(index: number): void {
  if (props.modelValue.length === 1) return // always keep at least one row
  emit(
    'update:modelValue',
    props.modelValue.filter((_, i) => i !== index),
  )
}

function addRow(): void {
  emit('update:modelValue', [
    ...props.modelValue,
    { id: `new-${Date.now()}`, description: '', quantity: 1, unitPrice: 0 },
  ])
}
</script>

<template>
  <div class="overflow-x-auto">
    <table class="w-full border-collapse">
      <thead>
        <tr class="border-b border-border-light bg-bg-secondary">
          <th class="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-text-muted">
            Description
          </th>
          <th class="px-3 py-2.5 text-right text-xs font-semibold uppercase tracking-wide text-text-muted">Qty</th>
          <th class="px-3 py-2.5 text-right text-xs font-semibold uppercase tracking-wide text-text-muted">
            Unit Price
          </th>
          <th class="px-3 py-2.5 text-right text-xs font-semibold uppercase tracking-wide text-text-muted">
            Amount
          </th>
          <th v-if="editable" class="no-print w-8"></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, index) in modelValue" :key="item.id" class="border-b border-border-light last:border-0">
          <td class="px-3 py-3 text-sm text-text-secondary">
            <EditableText
              :model-value="item.description"
              :editable="editable"
              placeholder="Description"
              @update:model-value="(v) => updateDescription(index, v)"
            />
          </td>
          <td class="px-3 py-3 text-right text-sm text-text-secondary">
            <EditableText
              :model-value="String(item.quantity)"
              :editable="editable"
              @update:model-value="(v) => updateQuantity(index, v)"
            />
          </td>
          <td class="px-3 py-3 text-right text-sm text-text-secondary">
            <EditableText
              :model-value="editable ? String(item.unitPrice) : formatCurrency(item.unitPrice, currency)"
              :editable="editable"
              @update:model-value="(v) => updateUnitPrice(index, v)"
            />
          </td>
          <td class="px-3 py-3 text-right text-sm font-medium text-text-primary">
            {{ formatCurrency(item.quantity * item.unitPrice, currency) }}
          </td>
          <td v-if="editable" class="no-print px-1 text-right">
            <button
              type="button"
              title="Remove line"
              class="text-text-muted hover:text-danger-600"
              :disabled="modelValue.length === 1"
              :class="modelValue.length === 1 ? 'cursor-not-allowed opacity-30' : ''"
              @click="removeRow(index)"
            >
              <Trash2 class="h-3.5 w-3.5" />
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <button
      v-if="editable"
      type="button"
      class="no-print mt-2 flex items-center gap-1 px-3 text-xs font-medium text-primary-700 hover:text-primary-900"
      @click="addRow"
    >
      <Plus class="h-3.5 w-3.5" /> Add Line Item
    </button>
  </div>
</template>
