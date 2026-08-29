<script setup lang="ts">
import { Plus, Trash2 } from '@lucide/vue'
import { reactive, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import IconButton from '@/components/common/IconButton.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useFormValidation } from '@/composables/useFormValidation'
import type { ContractClauseInput, ContractCreateInput } from '@/services/contractService'
import type { Project } from '@/types/Project'
import type { Quotation } from '@/types/Quotation'
import { validators } from '@/utils/validators'
import type { SelectOption } from '@/types/Ui'

const props = defineProps<{
  modelValue: boolean
  defaultClientRepresentative?: string
  loading?: boolean
  // When the project has services picked via ServicePickerDialog, prefill
  // contract value and scope summary from that breakdown. Superseded by
  // `quotation` below whenever one is available -- a quotation is what
  // was actually agreed/quoted, so it's the more authoritative source
  // once it exists.
  project?: Project
  // The project's current (selected, or latest) quotation. When present,
  // this is what "carries forward to the contract" in practice: currency,
  // value, client representative, and scope all default from here
  // instead of from the raw project service picks, so the contract
  // naturally continues from the quotation rather than starting from a
  // blank slate again.
  quotation?: Quotation
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: ContractCreateInput]
}>()

const CURRENCY_OPTIONS: SelectOption[] = [
  { label: 'KWD', value: 'KWD' },
  { label: 'USD', value: 'USD' },
  { label: 'EUR', value: 'EUR' },
]

function emptyClause(): ContractClauseInput {
  return { title: '', content: '' }
}

function emptyForm() {
  return {
    currency: 'KWD',
    contractValue: 0,
    expiryDate: '',
    clientRepresentative: '',
    scopeSummary: '',
    clauses: [] as ContractClauseInput[],
  }
}

// Prefills contract value from the project's serviceTotal and writes a
// one-line-per-activity scope summary -- fallback only, used when the
// project has no quotation yet. Still fully editable either way.
function scopeSummaryFromProject(project: Project | undefined): string {
  if (!project?.selectedActivities?.length) return ''
  return project.selectedActivities.map((item) => `${item.serviceName} - ${item.activityName}`).join('\n')
}

// Same idea, but from the quotation's own line items -- what was
// actually quoted, which is more authoritative than the project's raw
// service picks once a quotation exists.
function scopeSummaryFromQuotation(quotation: Quotation): string {
  if (!quotation.lineItems.length) return ''
  return quotation.lineItems.map((item) => item.description).join('\n')
}

const form = reactive(emptyForm())
const clauseErrors = reactive<string[]>([])
const { errors, setRules, validateAll } = useFormValidation()

setRules({
  contractValue: [validators.required('Contract value is required')],
  expiryDate: [validators.required('Expiry date is required')],
  clientRepresentative: [validators.required("Client representative's name is required")],
  scopeSummary: [validators.required('Scope summary is required')],
})

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    Object.assign(form, emptyForm())
    const quotation = props.quotation

    // A sensible starting point, not a locked value -- staff can still
    // change any of this if it needs to differ from the quotation.
    form.clientRepresentative = props.defaultClientRepresentative || ''
    form.contractValue = quotation?.amount ?? props.project?.serviceTotal ?? 0
    form.scopeSummary = quotation ? scopeSummaryFromQuotation(quotation) : scopeSummaryFromProject(props.project)

    if (quotation) {
      form.currency = quotation.currency
    }

    clauseErrors.splice(0, clauseErrors.length)
  },
)

function addClause(): void {
  form.clauses.push(emptyClause())
}

function removeClause(index: number): void {
  form.clauses.splice(index, 1)
}

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  const quotationId = props.quotation?.quotationNo ?? ''

  // Clauses are optional as a whole (many real contracts just use the
  // template's standard terms), but a clause that's been started can't
  // be saved half-empty -- both title and content are required once a
  // row exists at all.
  const itemErrors = form.clauses.map((clause) => {
    if (!clause.title.trim()) return 'Clause title is required'
    if (!clause.content.trim()) return 'Clause content is required'
    return ''
  })
  clauseErrors.splice(0, clauseErrors.length, ...itemErrors)
  const clausesValid = itemErrors.every((error) => !error)

  const formValid = validateAll(form)
  if (!formValid || !clausesValid) return

  emit('confirm', {
    projectId: '', // filled in by the caller, which already has the project in scope
    quotationId, // filled in from the eligible quotation the caller resolved for this dialog
    currency: form.currency,
    contractValue: form.contractValue,
    expiryDate: form.expiryDate,
    clientRepresentative: form.clientRepresentative.trim(),
    scopeSummary: form.scopeSummary.trim(),
    clauses: form.clauses.map((clause) => ({ title: clause.title.trim(), content: clause.content.trim() })),
  })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="New Contract" size="lg" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-5">
      <p v-if="quotation" class="text-xs text-text-muted">
        Prefilled from quotation {{ quotation.quotationNo }} -- currency, value, and scope below all carry over
        from it and can still be changed.
      </p>

      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
        <SelectBox v-model="form.currency" label="Currency" :options="CURRENCY_OPTIONS" />
        <NumberInput
          :model-value="form.contractValue"
          label="Contract Value"
          :min="0.01"
          step="0.01"
          required
          :error="errors.contractValue"
          @update:model-value="form.contractValue = Number($event)"
        />
        <DatePicker v-model="form.expiryDate" label="Expiry Date" required :error="errors.expiryDate" />
      </div>

      <TextInput
        v-model="form.clientRepresentative"
        label="Client Representative"
        placeholder="Name of the person signing for the client"
        required
        :error="errors.clientRepresentative"
      />

      <TextArea
        v-model="form.scopeSummary"
        label="Scope Summary"
        placeholder="Describe the scope of work covered by this contract"
        :rows="3"
        required
        :error="errors.scopeSummary"
      />

      <div class="flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <label class="text-sm font-medium text-text-secondary">Clauses (optional)</label>
          <BaseButton variant="ghost" size="sm" :icon="Plus" @click="addClause">Add Clause</BaseButton>
        </div>

        <div v-for="(clause, index) in form.clauses" :key="index" class="flex flex-col gap-2 rounded-lg border border-border-light p-3">
          <div class="flex items-start gap-2">
            <div class="flex-1">
              <TextInput v-model="clause.title" placeholder="Clause title" :error="clauseErrors[index]" />
            </div>
            <IconButton :icon="Trash2" :label="`Remove clause ${index + 1}`" size="sm" @click="removeClause(index)" />
          </div>
          <TextArea v-model="clause.content" placeholder="Clause content" :rows="2" />
        </div>
      </div>
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">Create Contract</BaseButton>
    </template>
  </BaseDialog>
</template>
