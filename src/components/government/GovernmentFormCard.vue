<script setup lang="ts">
import { CalendarClock, Languages, Sparkles } from '@lucide/vue'
import { computed } from 'vue'

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
  'ai-help': [form: GovernmentForm]
}>()

const authorityIcon = computed(() => (props.authority ? getAuthorityCategoryIcon(props.authority.category) : null))
const authorityName = computed(() => props.authority?.name ?? 'Unknown Authority')

const visibleDocuments = computed(() => props.form.requiredDocuments.slice(0, MAX_VISIBLE_DOCUMENTS))
const remainingDocumentCount = computed(() => props.form.requiredDocuments.length - visibleDocuments.value.length)
</script>

<template>
  <Card hoverable class="flex h-full flex-col">
    <div class="flex flex-1 flex-col gap-4">
      <div class="flex items-start justify-between gap-3">
        <div class="flex items-start gap-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-50">
            <component :is="authorityIcon" class="h-5 w-5 text-primary-600" />
          </span>
          <div class="flex flex-col gap-1">
            <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">
              {{ form.formCode }} · {{ form.version }}
            </p>
            <h3 class="text-base font-semibold leading-snug text-neutral-800">{{ form.title }}</h3>
          </div>
        </div>
        <IconButton :icon="Sparkles" label="Get AI help" variant="ghost" size="sm" @click="$emit('ai-help', form)" />
      </div>

      <p class="text-sm text-neutral-500">{{ form.description }}</p>

      <div class="flex flex-wrap items-center gap-2">
        <StatusBadge :label="form.category" :variant="getFormCategoryVariant(form.category)" />
        <span class="text-xs text-neutral-400">·</span>
        <span class="truncate text-xs font-medium text-neutral-500">{{ authorityName }}</span>
      </div>

      <div class="flex flex-col gap-1.5">
        <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Required Documents</p>
        <p class="text-sm text-neutral-600">
          {{ visibleDocuments.join(', ') }}
          <span v-if="remainingDocumentCount > 0" class="text-neutral-400"> +{{ remainingDocumentCount }} more</span>
        </p>
      </div>
    </div>

    <div class="mt-4 flex items-center justify-between border-t border-border-light pt-3 text-xs text-neutral-500">
      <div class="flex items-center gap-1.5">
        <Languages class="h-3.5 w-3.5" />
        <span>{{ form.language }}</span>
      </div>
      <div class="flex items-center gap-1.5">
        <CalendarClock class="h-3.5 w-3.5" />
        <span>Updated {{ formatDate(form.lastUpdated) }}</span>
      </div>
    </div>
  </Card>
</template>
