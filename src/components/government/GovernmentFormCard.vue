<script setup lang="ts">
import { CalendarClock, Languages, Pencil, RotateCcw, Sparkles, Trash2 } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import IconButton from '@/components/common/IconButton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { GovernmentAuthority, GovernmentForm } from '@/types/Government'
import { formatDate } from '@/utils/dateFormatter'
import { getAuthorityCategoryIcon, getFormCategoryVariant } from '@/utils/governmentFormHelpers'

const MAX_VISIBLE_DOCUMENTS = 2

const props = defineProps<{
  form: GovernmentForm
  authority?: GovernmentAuthority
}>()

defineEmits<{
  view: [form: GovernmentForm]
  'ai-help': [form: GovernmentForm]
  edit: [form: GovernmentForm]
  archive: [form: GovernmentForm]
  restore: [form: GovernmentForm]
}>()

const { t } = useI18n()

const authorityIcon = computed(() => (props.authority ? getAuthorityCategoryIcon(props.authority.category) : null))
const authorityName = computed(() => props.authority?.name ?? t('government.unknownAuthority'))
const isArchived = computed(() => props.form.status === 'Archived')

const visibleDocuments = computed(() => props.form.requiredDocuments.slice(0, MAX_VISIBLE_DOCUMENTS))
const remainingDocumentCount = computed(() => props.form.requiredDocuments.length - visibleDocuments.value.length)
</script>

<template>
  <Card hoverable class="flex h-full flex-col !p-0" :class="isArchived ? 'opacity-70' : ''">
    <button type="button" class="flex flex-1 flex-col gap-4 p-5 text-start" @click="$emit('view', form)">
      <div class="flex items-start justify-between gap-3">
        <div class="flex items-start gap-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-50">
            <component :is="authorityIcon" class="h-5 w-5 text-primary-600" />
          </span>
          <div class="flex flex-col gap-1">
            <p class="text-xs font-medium uppercase tracking-wide text-text-muted">
              {{ form.formCode }} · {{ form.version }}
            </p>
            <h3 class="text-base font-semibold leading-snug text-text-primary">{{ form.title }}</h3>
          </div>
        </div>
        <StatusBadge v-if="isArchived" :label="t('government.formStatus.archived')" variant="neutral" size="sm" />
      </div>

      <p class="text-sm text-text-muted">{{ form.description }}</p>

      <div class="flex flex-wrap items-center gap-2">
        <StatusBadge :label="form.category" :variant="getFormCategoryVariant(form.category)" />
        <span class="text-xs text-text-muted">·</span>
        <span class="truncate text-xs font-medium text-text-muted">{{ authorityName }}</span>
      </div>

      <div class="flex flex-col gap-1.5">
        <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('government.formCard.requiredDocuments') }}</p>
        <p class="text-sm text-text-secondary">
          {{ visibleDocuments.join(', ') }}
          <span v-if="remainingDocumentCount > 0" class="text-text-muted"> {{ t('government.formCard.moreCount', { count: remainingDocumentCount }) }}</span>
        </p>
      </div>

      <div class="mt-auto flex items-center gap-4 pt-1 text-xs text-text-muted">
        <span class="inline-flex items-center gap-1.5">
          <Languages class="h-3.5 w-3.5" />
          {{ form.language }}
        </span>
        <span class="inline-flex items-center gap-1.5">
          <CalendarClock class="h-3.5 w-3.5" />
          {{ t('government.formCard.updatedOn', { date: formatDate(form.lastUpdated) }) }}
        </span>
      </div>
    </button>

    <div class="flex items-center justify-end gap-1 border-t border-border-light px-3 py-2">
      <IconButton :icon="Sparkles" :label="t('government.formCard.getAiHelp')" variant="ghost" size="sm" @click="$emit('ai-help', form)" />
      <IconButton :icon="Pencil" :label="t('government.formCard.editForm')" variant="ghost" size="sm" @click="$emit('edit', form)" />
      <IconButton
        v-if="isArchived"
        :icon="RotateCcw"
        :label="t('government.formCard.restoreForm')"
        variant="ghost"
        size="sm"
        @click="$emit('restore', form)"
      />
      <IconButton
        v-else
        :icon="Trash2"
        :label="t('government.formCard.archiveForm')"
        variant="ghost"
        size="sm"
        @click="$emit('archive', form)"
      />
    </div>
  </Card>
</template>
