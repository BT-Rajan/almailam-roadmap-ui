<script setup lang="ts">
import { Plus, Trash2 } from '@lucide/vue'
import { computed, reactive, watch } from 'vue'

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
import { validators } from '@/utils/validators'
import type { SelectOption } from '@/types/Ui'
import { CONTRACT_TEMPLATE_LABELS, type ContractTemplateKey } from '@/types/Contract'
import { CONTRACT_LETTER_DEFAULTS } from '@/utils/contractLetterDefaults'

const props = defineProps<{
  modelValue: boolean
  defaultClientRepresentative?: string
  loading?: boolean
  // Same idea as NewQuotationDialog: when the project has services picked
  // via ServicePickerDialog, prefill contract value and scope summary from
  // that breakdown so the picked services carry through to the contract
  // too, instead of staff re-entering the total and typing out the scope
  // by hand. Still fully editable.
  project?: Project
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

const TEMPLATE_OPTIONS: SelectOption[] = [
  { label: 'Custom / Clause-based Contract', value: '' },
  ...Object.entries(CONTRACT_TEMPLATE_LABELS).map(([value, label]) => ({ label, value })),
]

function emptyClause(): ContractClauseInput {
  return { title: '', content: '' }
}

function emptyForm() {
  return {
    templateKey: '' as '' | ContractTemplateKey,
    templateName: '',
    currency: 'KWD',
    contractValue: 0,
    expiryDate: '',
    clientRepresentative: '',
    scopeSummary: '',
    clauses: [] as ContractClauseInput[],
    // Lettered-letter fields, only used when templateKey is set.
    subjectLineAr: '',
    subjectLineEn: '',
    projectReference: '',
    scopeItemsAr: [] as string[],
    scopeItemsEn: [] as string[],
    paymentTermsAr: [] as string[],
    paymentTermsEn: [] as string[],
  }
}

// Prefills contract value from the project's serviceTotal and writes a
// one-line-per-activity scope summary -- both still fully editable, this
// just saves re-typing what was already picked in the service picker.
function scopeSummaryFromProject(project: Project | undefined): string {
  if (!project?.selectedActivities?.length) return ''
  return project.selectedActivities.map((item) => `${item.serviceName} - ${item.activityName}`).join('\n')
}

const form = reactive(emptyForm())
const clauseErrors = reactive<string[]>([])
const { errors, setRules, validateAll } = useFormValidation()

setRules({
  templateName: [validators.required('Template name is required')],
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
    // A sensible starting point, not a locked value -- staff can still
    // change it if a different person signs for the client.
    form.clientRepresentative = props.defaultClientRepresentative ?? ''
    form.contractValue = props.project?.serviceTotal ?? 0
    form.scopeSummary = scopeSummaryFromProject(props.project)
    clauseErrors.splice(0, clauseErrors.length)
  },
)

// Picking a lettered template seeds the real bilingual scope/payment
// boilerplate from the source document, and the fee frequency it uses.
watch(
  () => form.templateKey,
  (key) => {
    if (!key) return
    const defaults = CONTRACT_LETTER_DEFAULTS[key]
    form.scopeItemsAr = [...defaults.scopeItemsAr]
    form.scopeItemsEn = [...defaults.scopeItemsEn]
    form.paymentTermsAr = [...defaults.paymentTermsAr]
    form.paymentTermsEn = [...defaults.paymentTermsEn]
  },
)

const isLettered = computed(() => form.templateKey !== '')

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
  if (isLettered.value) {
    // These two are required by the schema but not meaningful in
    // lettered mode -- auto-fill them from the template so validation
    // passes without asking the user to redundantly type them.
    form.templateName = CONTRACT_TEMPLATE_LABELS[form.templateKey as ContractTemplateKey]
    form.scopeSummary = form.scopeItemsEn.filter((line) => !line.startsWith('## ')).join('; ') || form.templateName
  }

  const formValid = validateAll(form)

  if (isLettered.value) {
    const lettererErrors: string[] = []
    if (!form.subjectLineAr.trim()) lettererErrors.push('Arabic subject line is required')
    if (!form.subjectLineEn.trim()) lettererErrors.push('English subject line is required')
    if (!formValid || lettererErrors.length) return

    emit('confirm', {
      projectId: '', // filled in by the caller, which already has the project in scope
      templateName: form.templateName,
      currency: form.currency,
      contractValue: form.contractValue,
      expiryDate: form.expiryDate,
      clientRepresentative: form.clientRepresentative.trim(),
      scopeSummary: form.scopeSummary,
      clauses: [],
      templateKey: form.templateKey || undefined,
      isBilingual: true,
      subjectLineAr: form.subjectLineAr.trim(),
      subjectLineEn: form.subjectLineEn.trim(),
      projectReference: form.projectReference.trim() || undefined,
      feeFrequency: CONTRACT_LETTER_DEFAULTS[form.templateKey as ContractTemplateKey].feeFrequency,
      scopeItemsAr: form.scopeItemsAr,
      scopeItemsEn: form.scopeItemsEn,
      paymentTermsAr: form.paymentTermsAr,
      paymentTermsEn: form.paymentTermsEn,
    })
    return
  }

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

  if (!formValid || !clausesValid) return

  emit('confirm', {
    projectId: '', // filled in by the caller, which already has the project in scope
    templateName: form.templateName.trim(),
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
      <SelectBox v-model="form.templateKey" label="Contract Format" :options="TEMPLATE_OPTIONS" />

      <template v-if="isLettered">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
          <SelectBox v-model="form.currency" label="Currency" :options="CURRENCY_OPTIONS" />
          <NumberInput
            :model-value="form.contractValue"
            :label="`Fee Amount${form.templateKey === 'supervision' ? ' / month' : ''}`"
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
          label="Recipient (السيد/ ...)"
          required
          :error="errors.clientRepresentative"
        />
        <TextInput v-model="form.projectReference" label="Project Reference (Plot / Parcel / Area)" />
        <TextInput v-model="form.subjectLineAr" label="Subject (Arabic)" required />
        <TextInput v-model="form.subjectLineEn" label="Subject (English)" required />
        <p class="text-xs text-text-muted">
          The contract prints the Arabic letter first, followed by its English translation, in the same document.
          Scope of work and payment terms are prefilled from the template and can be edited after the contract is
          created, before you finalize it.
        </p>
      </template>

      <template v-else>
      <TextInput v-model="form.templateName" label="Template Name" placeholder="e.g. Standard Consultancy Agreement" required :error="errors.templateName" />

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
            <IconButton :icon="Trash2" label="Remove clause" size="sm" @click="removeClause(index)" />
          </div>
          <TextArea v-model="clause.content" placeholder="Clause content" :rows="2" />
        </div>
      </div>
      </template>
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">Create Contract</BaseButton>
    </template>
  </BaseDialog>
</template>
