<script setup lang="ts">
import { ExternalLink, FileText, Pencil, Trash2 } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import IconButton from '@/components/common/IconButton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { GovernmentAuthority } from '@/types/Government'
import { getAuthorityCategoryIcon } from '@/utils/governmentFormHelpers'

const props = defineProps<{
  authority: GovernmentAuthority
  formCount: number
}>()

defineEmits<{
  open: [authority: GovernmentAuthority]
  edit: [authority: GovernmentAuthority]
  delete: [authority: GovernmentAuthority]
}>()

const { t } = useI18n()

const icon = computed(() => getAuthorityCategoryIcon(props.authority.category))

const AUTHORITY_CATEGORY_KEYS: Record<string, string> = {
  Municipality: 'governmentFormOptions.authorityCategory.municipality',
  'Fire Department': 'governmentFormOptions.authorityCategory.fireDepartment',
  Electricity: 'governmentFormOptions.authorityCategory.electricity',
  Water: 'governmentFormOptions.authorityCategory.water',
  Environment: 'governmentFormOptions.authorityCategory.environment',
  Internal: 'governmentFormOptions.authorityCategory.internal',
}

const categoryLabel = computed(() => {
  const key = AUTHORITY_CATEGORY_KEYS[props.authority.category]
  return key ? t(key) : props.authority.category
})
</script>

<template>
  <Card hoverable class="flex h-full flex-col !p-0">
    <button type="button" class="flex flex-1 flex-col gap-3 p-5 text-left" @click="$emit('open', authority)">
      <div class="flex items-start justify-between gap-3">
        <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-600">
          <component :is="icon" class="h-5 w-5" />
        </span>
        <StatusBadge :label="formCount === 1 ? t('government.authorityCard.formCountOne') : t('government.authorityCard.formCount', { count: formCount })" variant="neutral" size="sm" />
      </div>

      <div>
        <h3 class="text-base font-semibold leading-snug text-text-primary">{{ authority.name }}</h3>
        <p class="mt-0.5 text-xs font-medium text-text-muted">{{ categoryLabel }}</p>
      </div>

      <p class="line-clamp-2 flex-1 text-sm text-text-muted">{{ authority.description }}</p>

      <span class="inline-flex items-center gap-1.5 text-xs font-medium text-primary-600">
        <ExternalLink class="h-3.5 w-3.5" />
        {{ authority.website }}
      </span>
    </button>

    <div class="flex items-center justify-between gap-2 border-t border-border-light px-5 py-2.5">
      <span class="inline-flex items-center gap-1.5 text-xs text-text-muted">
        <FileText class="h-3.5 w-3.5" />
        {{ t('government.authorityCard.viewDocuments') }}
      </span>
      <div class="flex items-center gap-1">
        <IconButton :icon="Pencil" :label="t('government.authorityCard.editAuthority')" size="sm" variant="ghost" @click="$emit('edit', authority)" />
        <IconButton
          :icon="Trash2"
          :label="t('government.authorityCard.deleteAuthority')"
          size="sm"
          variant="ghost"
          @click="$emit('delete', authority)"
        />
      </div>
    </div>
  </Card>
</template>
