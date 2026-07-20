<script setup lang="ts">
import { CalendarClock, Languages, Pencil, Printer, RotateCcw, Trash2 } from '@lucide/vue'

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
        <h2 class="text-lg font-semibold text-neutral-800">{{ form.title }}</h2>
        <StatusBadge v-if="form.status === 'Archived'" label="Archived" variant="neutral" />
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <StatusBadge :label="form.category" :variant="getFormCategoryVariant(form.category)" />
        <span class="text-xs text-neutral-400">·</span>
        <span class="text-xs font-medium text-neutral-500">{{ authority?.name ?? 'Unknown Authority' }}</span>
      </div>

      <div class="flex items-center gap-4 text-xs text-neutral-500">
        <span class="inline-flex items-center gap-1.5">
          <Languages class="h-3.5 w-3.5" />
          {{ form.language }}
        </span>
        <span class="inline-flex items-center gap-1.5">
          <CalendarClock class="h-3.5 w-3.5" />
          Updated {{ formatDate(form.lastUpdated) }}
        </span>
      </div>

      <p class="text-sm text-neutral-600">{{ form.description }}</p>

      <div>
        <p class="mb-1.5 text-xs font-medium uppercase tracking-wide text-neutral-400">Required Documents</p>
        <ul class="list-inside list-disc text-sm text-neutral-600">
          <li v-for="document in form.requiredDocuments" :key="document">{{ document }}</li>
        </ul>
      </div>

      <Divider />

      <div>
        <p class="mb-2 text-xs font-medium uppercase tracking-wide text-neutral-400">Fillable Form</p>
        <iframe
          v-if="form.previewUrl"
          :src="form.previewUrl"
          title="Fillable form preview"
          class="h-[420px] w-full rounded-lg border border-border-light bg-white"
        />
        <EmptyState
          v-else
          title="No fillable sample attached"
          description="This form doesn't have a digital fillable sample yet. You can still print a summary sheet."
        />
      </div>
    </div>

    <template v-if="form" #footer>
      <BaseButton variant="secondary" :icon="Printer" @click="emit('print', form)">Print</BaseButton>
      <BaseButton
        v-if="form.status === 'Archived'"
        variant="secondary"
        :icon="RotateCcw"
        @click="emit('restore', form)"
      >
        Restore
      </BaseButton>
      <BaseButton v-else variant="secondary" :icon="Trash2" @click="emit('archive', form)">Archive</BaseButton>
      <BaseButton :icon="Pencil" @click="emit('edit', form)">Edit Form</BaseButton>
    </template>
  </BaseDrawer>
</template>
