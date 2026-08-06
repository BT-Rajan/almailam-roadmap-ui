<script setup lang="ts">
import { Printer } from '@lucide/vue'

import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import QuotationList from '@/components/project/QuotationList.vue'
import QuotationPreview from '@/components/project/QuotationPreview.vue'
import { useQuotationStore } from '@/stores/quotationStore'
import type { Client } from '@/types/Client'
import type { Project } from '@/types/Project'

defineProps<{
  project: Project
  client: Client | undefined
}>()

const quotationStore = useQuotationStore()

function handlePrint(): void {
  window.print()
}
</script>

<template>
  <div class="flex items-center justify-end">
    <BaseButton
      v-if="quotationStore.selectedQuotation"
      variant="secondary"
      size="sm"
      :icon="Printer"
      class="no-print"
      @click="handlePrint"
    >
      Print Quotation
    </BaseButton>
  </div>

  <div class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
    <div class="laptop:col-span-2 print:col-span-3">
      <EmptyState
        v-if="!quotationStore.selectedQuotation"
        title="No quotation selected"
        description="Select a quotation from the list to preview it."
      />
      <QuotationPreview
        v-else
        :quotation="quotationStore.selectedQuotation"
        :project="project"
        :client="client"
      />
    </div>

    <div class="no-print">
      <QuotationList
        :quotations="quotationStore.quotations"
        :selected-quotation-id="quotationStore.selectedQuotationId"
        @select="quotationStore.selectQuotation($event)"
      />
    </div>
  </div>
</template>
