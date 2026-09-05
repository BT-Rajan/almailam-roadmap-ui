<script setup lang="ts">
import { CalendarClock, Languages, Pencil, Printer, RotateCcw, Trash2 } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import Divider from '@/components/common/Divider.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { GovernmentAuthority, GovernmentForm } from '@/types/Government'
import { formatDate } from '@/utils/dateFormatter'
import { getFormCategoryVariant } from '@/utils/governmentFormHelpers'

interface Props {
  modelValue: boolean
  form?: GovernmentForm
  authority?: GovernmentAuthority
}

withDefaults(defineProps<Props>(), {
  form: undefined,
  authority: undefined,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  edit: [form: GovernmentForm]
  archive: [form: GovernmentForm]
  restore: [form: GovernmentForm]
  print: [form: GovernmentForm]
}>()

const { t } = useI18n()

const FORM_CATEGORY_KEYS: Record<string, string> = {
  'Building Permit': 'governmentFormOptions.formCategory.buildingPermit',
  'Occupancy Certificate': 'governmentFormOptions.formCategory.occupancyCertificate',
  'Fire Safety Approval': 'governmentFormOptions.formCategory.fireSafetyApproval',
  'Utility Connection': 'governmentFormOptions.formCategory.utilityConnection',
  'Environmental Clearance': 'governmentFormOptions.formCategory.environmentalClearance',
  'Business License': 'governmentFormOptions.formCategory.businessLicense',
  Agreement: 'governmentFormOptions.formCategory.agreement',
  'Legal Undertaking': 'governmentFormOptions.formCategory.legalUndertaking',
}

function categoryLabel(category: string): string {
  const key = FORM_CATEGORY_KEYS[category]
  return key ? t(key) : category
}
</script>

<template>
  <BaseDrawer
    :model-value="modelValue"
    :title="form ? `${form.formCode} \u00b7 ${form.version}` : undefined"
    width="lg"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div v-if="form" class="flex flex-col gap-5">
      <div class="flex flex-wrap items-center gap-2">
        <h2 class="text-lg font-semibold text-text-primary">{{ form.title }}</h2>
        <StatusBadge v-if="form.status === 'Archived'" :label="t('governmentFormOptions.statusFilter.archived')" variant="neutral" />
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <StatusBadge :label="categoryLabel(form.category)" :variant="getFormCategoryVariant(form.category)" />
        <span class="text-xs text-text-muted">·</span>
        <span class="text-xs font-medium text-text-muted">{{ authority?.name ?? t('government.unknownAuthority') }}</span>
      </div>

      <div class="flex items-center gap-4 text-xs text-text-muted">
        <span class="inline-flex items-center gap-1.5">
          <Languages class="h-3.5 w-3.5" />
          {{ form.language }}
        </span>
        <span class="inline-flex items-center gap-1.5">
          <CalendarClock class="h-3.5 w-3.5" />
          {{ t('government.formDetailDrawer.updated', { date: formatDate(form.lastUpdated) }) }}
        </span>
      </div>

      <p class="text-sm text-text-secondary">{{ form.description }}</p>

      <div>
        <p class="mb-1.5 text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('government.formDetailDrawer.requiredDocuments') }}</p>
        <ul class="list-inside list-disc text-sm text-text-secondary">
          <li v-for="document in form.requiredDocuments" :key="document">{{ document }}</li>
        </ul>
      </div>

      <Divider />

      <div>
        <p class="mb-2 text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('government.formDetailDrawer.fillableForm') }}</p>
        <iframe
          v-if="form.previewUrl"
          :src="form.previewUrl"
          :title="t('government.formDetailDrawer.fillableFormPreview')"
          class="h-[420px] w-full rounded-lg border border-border-light bg-white"
        />
        <EmptyState
          v-else
          :title="t('government.formDetailDrawer.noFillableSampleTitle')"
          :description="t('government.formDetailDrawer.noFillableSampleDescription')"
        />
      </div>
    </div>

    <template v-if="form" #footer>
      <BaseButton variant="secondary" :icon="Printer" @click="emit('print', form)">{{ t('common.print') }}</BaseButton>
      <BaseButton
        v-if="form.status === 'Archived'"
        variant="secondary"
        :icon="RotateCcw"
        @click="emit('restore', form)"
      >
        {{ t('government.formDetailDrawer.restore') }}
      </BaseButton>
      <BaseButton v-else variant="secondary" :icon="Trash2" @click="emit('archive', form)">{{ t('government.formDetailDrawer.archive') }}</BaseButton>
      <BaseButton :icon="Pencil" @click="emit('edit', form)">{{ t('government.formDetailDrawer.editForm') }}</BaseButton>
    </template>
  </BaseDrawer>
</template>
