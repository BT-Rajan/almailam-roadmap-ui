<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import { STANDARD_GOVERNMENT_FORMS } from '@/constants/standardGovernmentForms'
import type { GovernmentAuthority } from '@/types/Government'
import type { SelectOption } from '@/types/Ui'

interface Props {
  modelValue: boolean
  authorities: GovernmentAuthority[]
  // Form codes already present in the library -- pre-checked forms are
  // skipped and shown as "Already added" rather than offered again.
  existingFormCodes: string[]
  importing?: boolean
}

const props = withDefaults(defineProps<Props>(), { importing: false })

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  import: [payload: { authorityId: string; formCodes: string[] }]
}>()

const { t } = useI18n()

const selectedAuthorityId = ref('')
const selectedFormCodes = ref<string[]>([])

const authorityOptions = computed<SelectOption[]>(() =>
  props.authorities.map((authority) => ({ label: authority.name, value: authority.id })),
)

const availableForms = computed(() =>
  STANDARD_GOVERNMENT_FORMS.map((form) => ({
    ...form,
    alreadyAdded: props.existingFormCodes.includes(form.formCode),
  })),
)

watch(
  () => props.modelValue,
  (isOpen) => {
    if (!isOpen) return
    selectedAuthorityId.value = props.authorities[0]?.id ?? ''
    selectedFormCodes.value = availableForms.value.filter((form) => !form.alreadyAdded).map((form) => form.formCode)
  },
  { immediate: true },
)

function toggle(formCode: string): void {
  selectedFormCodes.value = selectedFormCodes.value.includes(formCode)
    ? selectedFormCodes.value.filter((code) => code !== formCode)
    : [...selectedFormCodes.value, formCode]
}

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleImport(): void {
  if (!selectedAuthorityId.value || selectedFormCodes.value.length === 0) return
  emit('import', { authorityId: selectedAuthorityId.value, formCodes: selectedFormCodes.value })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="t('administration.loadStandardFormsDialog.title')" size="lg" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <p class="text-sm text-text-secondary">
        {{ t('administration.loadStandardFormsDialog.description') }}
      </p>

      <EmptyState
        v-if="authorities.length === 0"
        :title="t('administration.loadStandardFormsDialog.noAuthorityTitle')"
        :description="t('administration.loadStandardFormsDialog.noAuthorityDescription')"
      />

      <template v-else>
        <SelectBox v-model="selectedAuthorityId" :label="t('administration.loadStandardFormsDialog.fileUnderAuthority')" :options="authorityOptions" required />

        <div class="flex flex-col rounded-lg border border-border-light">
          <div class="border-b border-border-light bg-bg-hover px-3 py-2 text-xs font-medium uppercase tracking-wide text-text-muted">
            {{ t('administration.loadStandardFormsDialog.standardFormsCount', { count: availableForms.length }) }}
          </div>
          <div class="max-h-96 overflow-y-auto p-2">
            <div
              v-for="form in availableForms"
              :key="form.formCode"
              class="flex items-start gap-2.5 rounded-md px-2 py-2"
              :class="form.alreadyAdded ? 'opacity-50' : 'hover:bg-bg-hover'"
            >
              <Checkbox
                :model-value="selectedFormCodes.includes(form.formCode)"
                :disabled="form.alreadyAdded"
                @update:model-value="toggle(form.formCode)"
              />
              <div class="min-w-0 flex-1">
                <p class="text-sm font-medium text-text-secondary">{{ form.title }}</p>
                <p class="text-xs text-text-muted">
                  {{ form.formCode }} · {{ form.category }}
                  <span v-if="form.alreadyAdded"> · {{ t('administration.loadStandardFormsDialog.alreadyAdded') }}</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="importing" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton
        :loading="importing"
        :disabled="authorities.length === 0 || !selectedAuthorityId || selectedFormCodes.length === 0"
        @click="handleImport"
      >
        {{ t('administration.loadStandardFormsDialog.addForms', selectedFormCodes.length) }}
      </BaseButton>
    </template>
  </BaseDialog>
</template>
