<script setup lang="ts">
import { Plus, Printer } from '@lucide/vue'
import { ref } from 'vue'

import AIResponseCard from '@/components/ai/AIResponseCard.vue'
import AISuggestionCard from '@/components/ai/AISuggestionCard.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import ContractList from '@/components/project/ContractList.vue'
import NewContractDialog from '@/components/project/NewContractDialog.vue'
import ContractPreview from '@/components/project/ContractPreview.vue'
import ContractRevisionHistory from '@/components/project/ContractRevisionHistory.vue'
import { useContractStore } from '@/stores/contractStore'
import { useToastStore } from '@/stores/toastStore'
import type { ContractCreateInput } from '@/services/contractService'
import type { Client } from '@/types/Client'
import type { Project } from '@/types/Project'

const props = defineProps<{
  project: Project
  client: Client | undefined
}>()

const contractStore = useContractStore()
const toastStore = useToastStore()

const isCreateDialogOpen = ref(false)
const isCreating = ref(false)

async function handleCreateContract(payload: ContractCreateInput): Promise<void> {
  isCreating.value = true
  try {
    const contract = await contractStore.createContract({ ...payload, projectId: props.project.id })
    toastStore.show('success', 'Contract created', `${contract.contractNo} was created successfully.`)
    isCreateDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to create contract', detail)
  } finally {
    isCreating.value = false
  }
}

function handlePrint(): void {
  window.print()
}
</script>

<template>
  <div class="flex items-center justify-between no-print">
    <BaseButton size="sm" :icon="Plus" @click="isCreateDialogOpen = true">New Contract</BaseButton>
    <BaseButton
      v-if="contractStore.selectedContract"
      variant="secondary"
      size="sm"
      :icon="Printer"
      @click="handlePrint"
    >
      Print Contract
    </BaseButton>
  </div>

  <EmptyState
    v-if="!contractStore.selectedContract"
    title="No contract selected"
    :description="contractStore.contracts.length === 0 ? 'Create the first contract for this project.' : 'Select a contract from the list to preview it.'"
    :action-label="contractStore.contracts.length === 0 ? 'New Contract' : undefined"
    @action="isCreateDialogOpen = true"
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

  <NewContractDialog
    v-model="isCreateDialogOpen"
    :project="project"
    :default-client-representative="client?.contactPerson"
    :loading="isCreating"
    @confirm="handleCreateContract"
  />
</template>
