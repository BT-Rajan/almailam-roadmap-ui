<script setup lang="ts">
import { FilePlus, MessageSquare } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import DetailPanel from '@/components/common/DetailPanel.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import ClientAddressCard from '@/components/client/ClientAddressCard.vue'
import ClientAuditTrail from '@/components/client/ClientAuditTrail.vue'
import ClientConsentList from '@/components/client/ClientConsentList.vue'
import ClientContactList from '@/components/client/ClientContactList.vue'
import ClientDocumentCard from '@/components/client/ClientDocumentCard.vue'
import ClientDocumentUploadDialog from '@/components/client/ClientDocumentUploadDialog.vue'
import ClientHeader from '@/components/client/ClientHeader.vue'
import ClientOnboardingProgress from '@/components/client/ClientOnboardingProgress.vue'
import ClientVerificationList from '@/components/client/ClientVerificationList.vue'
import ClientWorkspaceTabs from '@/components/client/ClientWorkspaceTabs.vue'
import ProjectCard from '@/components/project/ProjectCard.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useClientStore } from '@/stores/clientStore'
import { useProjectStore } from '@/stores/projectStore'
import type { ClientDocumentCategory, ClientWorkspaceTab, ClientWorkspaceTabKey } from '@/types/Client'
import { formatDate } from '@/utils/dateFormatter'

const route = useRoute()
const router = useRouter()
const clientStore = useClientStore()
const projectStore = useProjectStore()

const clientId = computed(() => route.params.clientId as string)
const activeTab = ref<ClientWorkspaceTabKey>('overview')
const isUploadDialogOpen = ref(false)

const TABS: ClientWorkspaceTab[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'contacts', label: 'Contacts' },
  { key: 'documents', label: 'Documents' },
  { key: 'verification', label: 'Verification' },
  { key: 'consent', label: 'Consent' },
  { key: 'projects', label: 'Projects' },
  { key: 'activity', label: 'Activity' },
]

const client = computed(() => clientStore.getClientById(clientId.value))
const clientProjects = computed(() => projectStore.projects.filter((project) => project.clientId === clientId.value))

const isLoading = computed(() => clientStore.isLoading || clientStore.isDetailLoading)
const error = computed(() => clientStore.error ?? clientStore.detailError)

const profileDetailItems = computed(() => {
  if (!client.value) return []
  if (client.value.clientType === 'Individual' && client.value.individualProfile) {
    const profile = client.value.individualProfile
    return [
      { label: 'Full Legal Name', value: profile.fullLegalName },
      { label: 'Preferred Name', value: profile.preferredName || '—' },
      { label: 'Nationality', value: profile.nationality },
      { label: 'Date of Birth', value: profile.dateOfBirth ? formatDate(profile.dateOfBirth) : '—' },
      { label: 'Country of Residence', value: profile.countryOfResidence },
    ]
  }
  if (client.value.organisationProfile) {
    const profile = client.value.organisationProfile
    return [
      { label: 'Legal Name', value: profile.legalName },
      { label: 'Trade Name', value: profile.tradeName || '—' },
      { label: 'Registration Number', value: profile.registrationNumber },
      { label: 'Trade Licence Number', value: profile.tradeLicenceNumber || '—' },
      { label: 'Country of Registration', value: profile.countryOfRegistration },
    ]
  }
  return []
})

const contactDetailItems = computed(() => {
  if (!client.value) return []
  return [
    { label: 'Contact Person', value: client.value.contactPerson },
    { label: 'Mobile', value: client.value.mobile },
    { label: 'Email', value: client.value.email },
    { label: 'City', value: client.value.city },
    { label: 'Preferred Channel', value: client.value.communicationPreference.preferredChannel },
  ]
})

async function loadData(): Promise<void> {
  if (clientStore.clients.length === 0) {
    await clientStore.loadClients()
  }
  await clientStore.loadClientDetail(clientId.value)
  if (projectStore.projects.length === 0) {
    await projectStore.loadProjects()
  }
}

onMounted(loadData)
watch(clientId, loadData)

function handleDocumentUpload(payload: { category: ClientDocumentCategory; title: string }): void {
  if (!client.value) return
  clientStore.addDocument({
    id: `CDOC-${Date.now()}`,
    clientId: client.value.id,
    category: payload.category,
    title: payload.title,
    version: 1,
    verificationStatus: 'Pending',
    uploadedBy: 'You',
    uploadDate: new Date().toISOString(),
  })
}

function openProject(projectId: string): void {
  router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId } })
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <ErrorState v-if="error" :description="error" @retry="loadData" />

    <template v-else-if="isLoading">
      <div class="rounded-xl border border-border-light bg-bg-card p-5">
        <SkeletonLoader :rows="4" />
      </div>
      <div class="rounded-xl border border-border-light bg-bg-card p-5">
        <SkeletonLoader :rows="8" />
      </div>
    </template>

    <EmptyState
      v-else-if="!client"
      title="Client not found"
      description="This client may have been removed or the link is incorrect."
    />

    <template v-else>
      <ClientHeader :client="client" />

      <ClientWorkspaceTabs :tabs="TABS" :active-tab="activeTab" @select="activeTab = $event" />

      <template v-if="activeTab === 'overview'">
        <div class="grid grid-cols-1 gap-6 laptop:grid-cols-2">
          <DetailPanel title="Profile Information" :items="profileDetailItems" />
          <div class="flex flex-col gap-3">
            <DetailPanel title="Contact Details" :items="contactDetailItems" />
            <BaseButton
              variant="secondary"
              size="sm"
              :icon="MessageSquare"
              class="no-print self-start"
              @click="router.push({ name: ROUTE_NAMES.MESSAGE_CENTRE, query: { clientId: client.id } })"
            >
              Message Client
            </BaseButton>
          </div>
          <ClientOnboardingProgress
            :client-type="client.clientType"
            :documents="clientStore.documents"
            :has-complete-profile="profileDetailItems.every((item) => item.value !== '—')"
          />
          <div class="flex flex-col gap-4">
            <ClientAddressCard v-for="address in clientStore.addresses" :key="address.id" :address="address" />
            <EmptyState
              v-if="clientStore.addresses.length === 0"
              title="No address on file"
              description="Add an address to complete this client's profile."
            />
          </div>
        </div>
      </template>

      <template v-else-if="activeTab === 'contacts'">
        <ClientContactList :contacts="clientStore.contacts" />
      </template>

      <template v-else-if="activeTab === 'documents'">
        <div class="flex items-center justify-end">
          <BaseButton size="sm" :icon="FilePlus" @click="isUploadDialogOpen = true">Add Document</BaseButton>
        </div>
        <EmptyState
          v-if="clientStore.documents.length === 0"
          title="No documents on file"
          description="Upload identity, registration or authorisation documents for this client."
          action-label="Add Document"
          @action="isUploadDialogOpen = true"
        />
        <div v-else class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
          <ClientDocumentCard v-for="document in clientStore.documents" :key="document.id" :document="document" />
        </div>
        <ClientDocumentUploadDialog v-model="isUploadDialogOpen" @upload="handleDocumentUpload" />
      </template>

      <template v-else-if="activeTab === 'verification'">
        <ClientVerificationList :verifications="clientStore.verifications" />
      </template>

      <template v-else-if="activeTab === 'consent'">
        <ClientConsentList :consents="clientStore.consents" />
      </template>

      <template v-else-if="activeTab === 'projects'">
        <EmptyState
          v-if="clientProjects.length === 0"
          title="No projects yet"
          description="Projects created for this client will appear here."
        />
        <div v-else class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
          <ProjectCard
            v-for="project in clientProjects"
            :key="project.id"
            :project="project"
            :client="client"
            @open="openProject"
          />
        </div>
      </template>

      <template v-else-if="activeTab === 'activity'">
        <ClientAuditTrail :events="clientStore.auditEvents" />
      </template>
    </template>
  </div>
</template>
