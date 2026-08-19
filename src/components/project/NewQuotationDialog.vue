<script setup lang="ts">
import { Plus, Trash2 } from '@lucide/vue'
import { computed, reactive, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import Divider from '@/components/common/Divider.vue'
import IconButton from '@/components/common/IconButton.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useFormValidation } from '@/composables/useFormValidation'
import type { QuotationCreateInput, QuotationLineItemInput } from '@/services/quotationService'
import type { Project } from '@/types/Project'
import { formatCurrency } from '@/utils/currencyFormatter'
import { validators } from '@/utils/validators'
import type { SelectOption } from '@/types/Ui'

const props = defineProps<{
  modelValue: boolean
  loading?: boolean
  // When the project this quotation is for has services picked via
  // ServicePickerDialog, prefill the line items from that breakdown --
  // this is what "carries forward to the quotation" in practice, since
  // staff would otherwise be re-typing the same services and prices by
  // hand. Still fully editable afterwards; this only seeds the form.
  project?: Project
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: QuotationCreateInput]
}>()

const CURRENCY_OPTIONS: SelectOption[] = [
  { label: 'KWD', value: 'KWD' },
  { label: 'USD', value: 'USD' },
  { label: 'AED', value: 'AED' },
  { label: 'EUR', value: 'EUR' },
]

interface DraftLineItem {
  description: string
  quantity: number
  unitPrice: number
}

function emptyLineItem(): DraftLineItem {
  return { description: '', quantity: 1, unitPrice: 0 }
}

function emptyForm() {
  return {
    validity: '',
    currency: 'KWD',
    taxRatePercent: 0,
    discountAmount: 0,
    notes: '',
    termsText: '',
    lineItems: [emptyLineItem()] as DraftLineItem[],
  }
}

// Turns the project's picked activities into draft line items (one per
// activity, quantity 1, unit price = the picked fixedCost). Falls back to
// emptyForm()'s single blank row when the project has no picks yet, so
// staff building a quotation for an older/manual project see the exact
// same starting point as before.
function formFromProject(project: Project | undefined) {
  if (!project?.selectedActivities?.length) return emptyForm()
  return {
    ...emptyForm(),
    lineItems: project.selectedActivities.map((item) => ({
      description: `${item.serviceName} - ${item.activityName}`,
      quantity: 1,
      unitPrice: item.fixedCost,
    })),
  }
}

const form = reactive(formFromProject(props.project))
const lineItemErrors = reactive<string[]>([])
const { errors, setRules, validateAll } = useFormValidation()

setRules({
  validity: [validators.required('Validity date is required')],
})

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    Object.assign(form, formFromProject(props.project))
    lineItemErrors.splice(0, lineItemErrors.length)
  },
)

function addLineItem(): void {
  form.lineItems.push(emptyLineItem())
}

function removeLineItem(index: number): void {
  if (form.lineItems.length === 1) return // always keep at least one row
  form.lineItems.splice(index, 1)
}

// Mirrors utils/quotationHelpers.ts's calculateQuotationPricing() exactly,
// so what staff see while building the quotation matches what the
// preview/print view shows once it's created.
const subtotal = computed(() => form.lineItems.reduce((sum, item) => sum + item.quantity * item.unitPrice, 0))
const taxableAmount = computed(() => subtotal.value - form.discountAmount)
const taxAmount = computed(() => (taxableAmount.value * form.taxRatePercent) / 100)
const total = computed(() => taxableAmount.value + taxAmount.value)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  const formValid = validateAll(form)

  const itemErrors = form.lineItems.map((item) => {
    if (!item.description.trim()) return 'Description is required'
    if (item.quantity <= 0) return 'Quantity must be greater than 0'
    if (item.unitPrice < 0) return 'Unit price cannot be negative'
    return ''
  })
  lineItemErrors.splice(0, lineItemErrors.length, ...itemErrors)
  const lineItemsValid = itemErrors.every((error) => !error)

  if (!formValid || !lineItemsValid) return

  const lineItems: QuotationLineItemInput[] = form.lineItems.map((item) => ({
    description: item.description.trim(),
    quantity: item.quantity,
    unitPrice: item.unitPrice,
  }))

  emit('confirm', {
    projectId: '', // filled in by the caller, which already has the project in scope
    validity: form.validity,
    currency: form.currency,
    taxRatePercent: form.taxRatePercent,
    discountAmount: form.discountAmount,
    notes: form.notes.trim() || undefined,
    termsAndConditions: form.termsText
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0),
    lineItems,
  })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="New Quotation" size="lg" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-5">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
        <DatePicker v-model="form.validity" label="Valid Until" required :error="errors.validity" />
        <SelectBox v-model="form.currency" label="Currency" :options="CURRENCY_OPTIONS" />
        <NumberInput
          :model-value="form.taxRatePercent"
          label="Tax Rate (%)"
          :min="0"
          :max="100"
          step="0.1"
          @update:model-value="form.taxRatePercent = Number($event)"
        />
      </div>

      <div class="flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <label class="text-sm font-medium text-neutral-700">Line Items</label>
          <BaseButton variant="ghost" size="sm" :icon="Plus" @click="addLineItem">Add Line Item</BaseButton>
        </div>

        <div v-for="(item, index) in form.lineItems" :key="index" class="flex flex-col gap-2 rounded-lg border border-border-light p-3">
          <div class="flex items-start gap-2">
            <div class="flex-1">
              <TextInput v-model="item.description" placeholder="Description" :error="lineItemErrors[index]" />
            </div>
            <IconButton
              :icon="Trash2"
              label="Remove line item"
              size="sm"
              :disabled="form.lineItems.length === 1"
              @click="removeLineItem(index)"
            />
          </div>
          <div class="grid grid-cols-2 gap-2">
            <NumberInput
              :model-value="item.quantity"
              placeholder="Quantity"
              :min="0.01"
              step="0.01"
              @update:model-value="item.quantity = Number($event)"
            />
            <NumberInput
              :model-value="item.unitPrice"
              placeholder="Unit Price"
              :min="0"
              step="0.01"
              @update:model-value="item.unitPrice = Number($event)"
            />
          </div>
          <p class="text-right text-xs text-neutral-500">
            {{ formatCurrency(item.quantity * item.unitPrice, form.currency) }}
          </p>
        </div>
      </div>

      <NumberInput
        :model-value="form.discountAmount"
        label="Discount Amount"
        :min="0"
        step="0.01"
        @update:model-value="form.discountAmount = Number($event)"
      />

      <TextArea v-model="form.notes" label="Notes" placeholder="Optional notes for this quotation" :rows="2" />
      <TextArea
        v-model="form.termsText"
        label="Terms &amp; Conditions"
        placeholder="One term per line"
        hint="Each line becomes a separate term."
        :rows="3"
      />

      <Divider />

      <div class="flex flex-col gap-2 text-sm">
        <div class="flex items-center justify-between text-neutral-600">
          <span>Subtotal</span>
          <span class="font-medium text-neutral-800">{{ formatCurrency(subtotal, form.currency) }}</span>
        </div>
        <div v-if="form.discountAmount > 0" class="flex items-center justify-between text-neutral-600">
          <span>Discount</span>
          <span class="font-medium text-danger-700">-{{ formatCurrency(form.discountAmount, form.currency) }}</span>
        </div>
        <div class="flex items-center justify-between text-neutral-600">
          <span>Tax ({{ form.taxRatePercent }}%)</span>
          <span class="font-medium text-neutral-800">{{ formatCurrency(taxAmount, form.currency) }}</span>
        </div>
        <Divider />
        <div class="flex items-center justify-between">
          <span class="text-sm font-semibold text-neutral-800">Total</span>
          <span class="text-lg font-semibold text-primary-700">{{ formatCurrency(total, form.currency) }}</span>
        </div>
      </div>
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">Create Quotation</BaseButton>
    </template>
  </BaseDialog>
</template>
