<script setup lang="ts">
import { FileSignature } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import Divider from '@/components/common/Divider.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { getContractStatusVariant } from '@/utils/contractHelpers'
import type { Client } from '@/types/Client'
import type { Contract } from '@/types/Contract'
import type { Project } from '@/types/Project'

interface Props {
  contract: Contract
  project: Project
  client?: Client
}

withDefaults(defineProps<Props>(), {
  client: undefined,
})
</script>

<template>
  <Card class="print:shadow-none" :padded="true">
    <div id="contract-print-area" class="flex flex-col gap-6">
      <div class="flex flex-col gap-4 tablet:flex-row tablet:items-start tablet:justify-between">
        <div class="flex items-center gap-3">
          <span class="flex h-11 w-11 items-center justify-center rounded-lg bg-primary-50 text-primary-700">
            <FileSignature class="h-5 w-5" />
          </span>
          <div>
            <p class="text-sm font-semibold text-text-primary">Almailam Engineering Consultants</p>
            <p class="text-xs text-text-muted">Engineering Design & Government Approvals</p>
          </div>
        </div>

        <div class="flex flex-col gap-1 tablet:items-end">
          <div class="flex items-center gap-2">
            <h2 class="text-lg font-semibold text-text-primary">{{ contract.contractNo }}</h2>
            <StatusBadge :label="contract.status" :variant="getContractStatusVariant(contract.status)" />
          </div>
          <p class="text-xs text-text-muted">Revision {{ contract.revision }} · {{ contract.templateName }}</p>
        </div>
      </div>

      <Divider />

      <div class="grid grid-cols-1 gap-6 tablet:grid-cols-3">
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Client</p>
          <p class="text-sm font-semibold text-text-primary">{{ client?.companyName ?? 'Unknown Client' }}</p>
          <p class="text-sm text-text-muted">Represented by {{ contract.clientRepresentative }}</p>
        </div>
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Project</p>
          <p class="text-sm font-semibold text-text-primary">{{ project.projectName }}</p>
          <p class="text-sm text-text-muted">{{ project.projectNo }} · {{ project.service }}</p>
        </div>
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Dates</p>
          <p class="text-sm text-text-muted">Issued: {{ formatDate(contract.issueDate) }}</p>
          <p v-if="contract.signedDate" class="text-sm text-text-muted">
            Signed: {{ formatDate(contract.signedDate) }}
          </p>
          <p class="text-sm text-text-muted">Expires: {{ formatDate(contract.expiryDate) }}</p>
        </div>
      </div>

      <Divider />

      <div class="flex flex-col gap-2">
        <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Scope Summary</p>
        <p class="text-sm leading-relaxed text-text-secondary">{{ contract.scopeSummary }}</p>
      </div>

      <div class="flex items-center justify-between rounded-lg bg-bg-secondary px-4 py-3">
        <span class="text-sm font-medium text-text-secondary">Contract Value</span>
        <span class="text-lg font-semibold text-primary-700">
          {{ formatCurrency(contract.contractValue, contract.currency) }}
        </span>
      </div>

      <div class="flex flex-col gap-4">
        <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Clauses</p>
        <div
          v-for="(clause, index) in contract.clauses"
          :key="clause.id"
          class="flex flex-col gap-1 border-b border-border-light pb-4 last:border-0 last:pb-0"
        >
          <p class="text-sm font-semibold text-text-primary">{{ index + 1 }}. {{ clause.title }}</p>
          <p class="text-sm leading-relaxed text-text-secondary">{{ clause.content }}</p>
        </div>
      </div>

      <p class="no-print text-center text-xs text-text-muted">
        This is a prototype preview. Final legal documents are prepared and issued outside this system.
      </p>
    </div>
  </Card>
</template>
