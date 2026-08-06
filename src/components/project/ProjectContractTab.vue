<script setup lang="ts">
import { Printer } from '@lucide/vue'

import AIResponseCard from '@/components/ai/AIResponseCard.vue'
import AISuggestionCard from '@/components/ai/AISuggestionCard.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import ContractList from '@/components/project/ContractList.vue'
import ContractPreview from '@/components/project/ContractPreview.vue'
import ContractRevisionHistory from '@/components/project/ContractRevisionHistory.vue'
import { useContractStore } from '@/stores/contractStore'
import type { Client } from '@/types/Client'
import type { Project } from '@/types/Project'

defineProps<{
  project: Project
  client: Client | undefined
}>()

const contractStore = useContractStore()

function handlePrint(): void {
  window.print()
}
</script>

<template>
  <div class="flex items-center justify-end">
    <BaseButton
      v-if="contractStore.selectedContract"
      variant="secondary"
      size="sm"
      :icon="Printer"
      class="no-print"
      @click="handlePrint"
    >
      Print Contract
    </BaseButton>
  </div>

  <EmptyState
    v-if="!contractStore.selectedContract"
    title="No contract selected"
    description="Select a contract from the list to preview it."
  />

  <div v-else class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
    <div class="flex flex-col gap-6 laptop:col-span-2 print:col-span-3">
      <ContractPreview
        :contract="contractStore.selectedContract"
        :project="project"
        :client="client"
      />

      <div class="no-print">
        <AIResponseCard
          v-if="contractStore.aiSummary"
          title="AI Contract Summary"
          :summary="contractStore.aiSummary.summary"
          :details="contractStore.aiSummary.details"
          :confidence="contractStore.aiSummary.confidence"
        />
        <div v-else-if="contractStore.isAiSummaryLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
          <SkeletonLoader :rows="3" />
        </div>
      </div>

      <AISuggestionCard
        v-if="contractStore.aiSummary?.suggestions.length"
        class="no-print"
        :suggestions="contractStore.aiSummary.suggestions"
      />
    </div>

    <div class="flex flex-col gap-6 no-print">
      <ContractList
        :contracts="contractStore.contracts"
        :selected-contract-id="contractStore.selectedContractId"
        @select="contractStore.selectContract($event)"
      />
      <ContractRevisionHistory :revisions="contractStore.selectedContract.revisions" />
    </div>
  </div>
</template>
