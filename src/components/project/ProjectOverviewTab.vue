<script setup lang="ts">
import { AlertTriangle, MessageSquare } from '@lucide/vue'
import { computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import DetailPanel from '@/components/common/DetailPanel.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useClientStore } from '@/stores/clientStore'
import { useContractStore } from '@/stores/contractStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useToastStore } from '@/stores/toastStore'
import type { Client } from '@/types/Client'
import type { Project, ProjectWorkspaceTabKey } from '@/types/Project'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { getClientVerificationVariant } from '@/utils/clientHelpers'

const props = defineProps<{
  project: Project
  client: Client | undefined
}>()

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
}>()

const router = useRouter()
const clientStore = useClientStore()
const quotationStore = useQuotationStore()
const contractStore = useContractStore()
const toastStore = useToastStore()

const projectDetailItems = computed(() => [
  { label: 'Service', value: props.project.service },
  { label: 'Field Engineer', value: props.project.engineer },
  { label: 'Start Date', value: formatDate(props.project.startDate) },
  { label: 'Target Completion Date', value: formatDate(props.project.targetDate) },
  { label: 'Current Stage', value: props.project.currentStage },
  { label: 'Priority', value: props.project.priority },
])

const clientDetailItems = computed(() => {
  if (!props.client) return []
  return [
    { label: 'Company Name', value: props.client.companyName },
    { label: 'Contact Person', value: props.client.contactPerson },
    { label: 'Mobile', value: props.client.mobile },
    { label: 'Email', value: props.client.email },
    { label: 'City', value: props.client.city },
  ]
})

const hasScope = computed(
  () =>
    Boolean(props.project.description) ||
    (props.project.selectedActivities && props.project.selectedActivities.length > 0) ||
    (props.project.selectedTypeActivities && props.project.selectedTypeActivities.length > 0),
)

// Civil ID verification -- only needed at the Quotation stage's overview
// (see the Card below), so only fetched then rather than on every visit
// to this tab regardless of stage. The client's onboarding documents
// aren't loaded anywhere else in the project workspace.
function loadClientDetailIfNeeded(): void {
  if (props.project.currentStage === 'Quotation' && props.client) {
    clientStore.loadClientDetail(props.client.id)
  }
}
onMounted(loadClientDetailIfNeeded)
watch(() => [props.project.currentStage, props.client?.id], loadClientDetailIfNeeded)

// Civil ID is filed under the 'Identity Document' category regardless of
// the client's actual document-type label -- see
// getDocumentCategoryForIdentificationType (constants/clientOptions.ts).
const civilIdDocument = computed(() => clientStore.documents.find((document) => document.category === 'Identity Document'))

function viewCivilIdDocument(): void {
  if (!props.client || !civilIdDocument.value) return
  clientStore.viewDocument(props.client.id, civilIdDocument.value.id).catch(() => {
    toastStore.show('error', 'Failed to open document', 'Please try again.')
  })
}

const latestQuotation = computed(() => quotationStore.latestQuotation)

// The contract's own linked quotation (contract.quotationNo) rather than
// quotationStore.latestQuotation -- once a contract exists it should
// always point at exactly the quotation it was generated from, not
// whichever quotation happens to be newest (a later draft revision could
// otherwise show here despite never having been the one approved).
const latestContract = computed(() => contractStore.latestContract)
const contractQuotation = computed(() =>
  latestContract.value?.quotationNo
    ? quotationStore.quotations.find((quotation) => quotation.quotationNo === latestContract.value?.quotationNo)
    : undefined,
)
</script>

<template>
  <div class="flex flex-col gap-6">
    <Card v-if="hasScope">
      <template #header>
        <h3 class="text-sm font-semibold text-text-primary">Scope</h3>
      </template>
      <p v-if="project.description" class="whitespace-pre-wrap text-sm text-text-secondary">{{ project.description }}</p>

      <div v-if="project.selectedActivities && project.selectedActivities.length > 0" class="mt-3 border-t border-border-light pt-3">
        <p class="mb-1.5 text-xs font-medium uppercase tracking-wide text-text-muted">Services</p>
        <ul class="flex flex-col gap-1">
          <li
            v-for="item in project.selectedActivities"
            :key="item.activityId"
            class="flex items-center justify-between gap-3 text-sm text-text-secondary"
          >
            <span>{{ item.activityName }}</span>
            <span class="shrink-0 text-text-muted">{{ formatCurrency(item.fixedCost) }}</span>
          </li>
        </ul>
      </div>

      <div v-if="project.selectedTypeActivities && project.selectedTypeActivities.length > 0" class="mt-3 border-t border-border-light pt-3">
        <p class="mb-1.5 text-xs font-medium uppercase tracking-wide text-text-muted">Additional Services</p>
        <ul class="flex flex-col gap-1">
          <li
            v-for="item in project.selectedTypeActivities"
            :key="item.id"
            class="flex items-center justify-between gap-3 text-sm text-text-secondary"
          >
            <span>{{ item.activityName }}</span>
            <span class="shrink-0 text-text-muted">{{ item.isCoveredByService ? 'Covered by service' : formatCurrency(item.cost) }}</span>
          </li>
        </ul>
      </div>
    </Card>

    <Card v-if="project.currentStage === 'Quotation'">
      <template #header>
        <h3 class="text-sm font-semibold text-text-primary">Quotation</h3>
      </template>
      <div class="flex flex-col gap-4">
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm text-text-secondary">Quotation Status</span>
          <StatusBadge
            v-if="latestQuotation"
            :label="latestQuotation.status"
            :variant="latestQuotation.status === 'Approved' ? 'success' : latestQuotation.status === 'Rejected' ? 'danger' : 'neutral'"
          />
          <span v-else class="text-sm text-text-muted">No quotation yet</span>
        </div>

        <div class="flex flex-col items-start justify-between gap-3 rounded-lg border border-warning-100 bg-warning-50 px-3 py-2.5 tablet:flex-row tablet:items-center">
          <div class="flex items-center gap-2 text-sm text-warning-700">
            <AlertTriangle class="h-4 w-4 shrink-0" />
            <span>Civil ID verification is a must</span>
            <StatusBadge
              v-if="civilIdDocument"
              :label="civilIdDocument.verificationStatus"
              :variant="getClientVerificationVariant(civilIdDocument.verificationStatus)"
            />
            <span v-else class="text-warning-700">-- not uploaded yet</span>
          </div>
          <BaseButton v-if="civilIdDocument" variant="ghost" size="sm" class="no-print" @click="viewCivilIdDocument">
            View Civil ID Attachment
          </BaseButton>
        </div>

        <div class="flex justify-end no-print">
          <BaseButton variant="secondary" size="sm" @click="emit('navigate-tab', 'quotation')">Go to Quotation</BaseButton>
        </div>
      </div>
    </Card>

    <Card v-if="project.currentStage === 'Contract'">
      <template #header>
        <h3 class="text-sm font-semibold text-text-primary">Contract</h3>
      </template>
      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
          <div>
            <p class="text-xs text-text-muted">Quotation Number</p>
            <p class="text-sm font-medium text-text-primary">{{ contractQuotation?.quotationNo ?? '—' }}</p>
          </div>
          <div>
            <p class="text-xs text-text-muted">Quotation Date</p>
            <p class="text-sm font-medium text-text-primary">{{ contractQuotation ? formatDate(contractQuotation.issueDate) : '—' }}</p>
          </div>
          <div>
            <p class="text-xs text-text-muted">Quotation Amount</p>
            <p class="text-sm font-medium text-text-primary">{{ contractQuotation ? formatCurrency(contractQuotation.amount) : '—' }}</p>
          </div>
        </div>

        <div class="flex flex-col items-start justify-between gap-3 rounded-lg border border-warning-100 bg-warning-50 px-3 py-2.5 tablet:flex-row tablet:items-center">
          <div class="flex items-center gap-2 text-sm text-warning-700">
            <AlertTriangle class="h-4 w-4 shrink-0" />
            <span>Quotation approval is a must</span>
            <StatusBadge
              v-if="contractQuotation"
              :label="contractQuotation.status"
              :variant="contractQuotation.status === 'Approved' ? 'success' : contractQuotation.status === 'Rejected' ? 'danger' : 'neutral'"
            />
            <span v-else class="text-warning-700">-- no quotation linked</span>
          </div>
          <BaseButton v-if="contractQuotation" variant="ghost" size="sm" class="no-print" @click="emit('navigate-tab', 'quotation')">
            View Approved Quotation
          </BaseButton>
        </div>
      </div>
    </Card>

    <div class="grid grid-cols-1 gap-6 laptop:grid-cols-2">
      <DetailPanel title="Project Details" :items="projectDetailItems" />
      <div class="flex flex-col gap-3">
        <DetailPanel title="Client Details" :items="clientDetailItems" />
        <div class="flex gap-2 no-print">
          <BaseButton
            v-if="client"
            variant="secondary"
            size="sm"
            :icon="MessageSquare"
            @click="router.push({ name: ROUTE_NAMES.MESSAGE_CENTRE, query: { clientId: client.id } })"
          >
            Message Client
          </BaseButton>
          <BaseButton
            v-if="client"
            variant="ghost"
            size="sm"
            @click="router.push({ name: ROUTE_NAMES.CLIENT_WORKSPACE, params: { clientId: client.id } })"
          >
            View Full Profile
          </BaseButton>
        </div>
      </div>
    </div>
  </div>
</template>
