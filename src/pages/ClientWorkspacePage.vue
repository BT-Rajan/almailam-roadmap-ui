<script setup lang="ts">
import { FilePlus, MessageSquare, ShieldCheck } from '@lucide/vue'
import { computed, defineAsyncComponent, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import DetailPanel from '@/components/common/DetailPanel.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import ClientAddressCard from '@/components/client/ClientAddressCard.vue'
import ClientEditDialog from '@/components/client/ClientEditDialog.vue'
import ClientHeader from '@/components/client/ClientHeader.vue'
import ClientOnboardingActions from '@/components/client/ClientOnboardingActions.vue'
import ClientOnboardingProgress from '@/components/client/ClientOnboardingProgress.vue'
import ClientOnboardingStatusDialog from '@/components/client/ClientOnboardingStatusDialog.vue'
import ClientWorkspaceTabs from '@/components/client/ClientWorkspaceTabs.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'

// Lazy-loaded: only fetched when the user opens that tab (see ProjectWorkspacePage
// for the same pattern applied to the project workspace).
const ClientContactList = defineAsyncComponent(() => import('@/components/client/ClientContactList.vue'))
const ClientIdentificationList = defineAsyncComponent(() => import('@/components/client/ClientIdentificationList.vue'))
const ClientDocumentCard = defineAsyncComponent(() => import('@/components/client/ClientDocumentCard.vue'))
const ClientDocumentUploadDialog = defineAsyncComponent(() => import('@/components/client/ClientDocumentUploadDialog.vue'))
const ClientVerificationList = defineAsyncComponent(() => import('@/components/client/ClientVerificationList.vue'))
const ClientVerificationDialog = defineAsyncComponent(() => import('@/components/client/ClientVerificationDialog.vue'))
const ClientConsentList = defineAsyncComponent(() => import('@/components/client/ClientConsentList.vue'))
const ClientAuditTrail = defineAsyncComponent(() => import('@/components/client/ClientAuditTrail.vue'))
const ProjectCard = defineAsyncComponent(() => import('@/components/project/ProjectCard.vue'))
import { useClientStore } from '@/stores/clientStore'
import { useProjectStore } from '@/stores/projectStore'
import { useToastStore } from '@/stores/toastStore'
import type { ClientDocument, ClientDocumentCategory, ClientOnboardingState, ClientVerificationResult, ClientWorkspaceTab, ClientWorkspaceTabKey } from '@/types/Client'
import type { ClientEditForm } from '@/utils/clientValidation'
import { formatDate } from '@/utils/dateFormatter'

const route = useRoute()
const router = useRouter()
const clientStore = useClientStore()
const projectStore = useProjectStore()
const toastStore = useToastStore()

const clientId = computed(() => route.params.clientId as string)
const activeTab = ref<ClientWorkspaceTabKey>('overview')
const isUploadDialogOpen = ref(false)
const isStatusDialogOpen = ref(false)
const isOnboardingStateSaving = ref(false)
const isVerificationDialogOpen = ref(false)
const isVerificationSaving = ref(false)
const verificationDialogTarget = ref<ClientDocument | null>(null)
const isEditDialogOpen = ref(false)
const isEditSaving = ref(false)

const TABS: ClientWorkspaceTab[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'contacts', label: 'Contacts' },
  { key: 'identification', label: 'Identification' },
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

const hasCompleteProfile = computed(() => profileDetailItems.value.every((item) => item.value !== '—'))

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

async function handleDocumentUpload(payload: { category: ClientDocumentCategory; title: string; file: File }): Promise<void> {
  if (!client.value) return
  try {
    await clientStore.createDocument(client.value.id, {
      category: payload.category,
      title: payload.title,
      file: payload.file,
    })
    toastStore.show('success', 'Document added', `${payload.title} was uploaded successfully.`)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to upload document', detail)
  }
}

async function handleDocumentDownload(document: ClientDocument): Promise<void> {
  if (!client.value) return
  try {
    await clientStore.downloadDocument(client.value.id, document.id, document.originalFilename)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to download document', detail)
  }
}

async function applyOnboardingState(nextState: ClientOnboardingState, reason?: string): Promise<void> {
  if (!client.value) return
  isOnboardingStateSaving.value = true
  try {
    await clientStore.setOnboardingState(client.value.id, nextState, reason)
    toastStore.show('success', 'Onboarding status updated', `Status changed to "${nextState}".`)
    isStatusDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to update onboarding status', detail)
  } finally {
    isOnboardingStateSaving.value = false
  }
}

function handleAdvanceOnboarding(nextState: ClientOnboardingState): void {
  void applyOnboardingState(nextState)
}

function handleConfirmStatusChange(payload: { onboardingState: ClientOnboardingState; reason?: string }): void {
  void applyOnboardingState(payload.onboardingState, payload.reason)
}

function openVerificationDialog(document?: ClientDocument): void {
  verificationDialogTarget.value = document ?? null
  isVerificationDialogOpen.value = true
}

async function handleConfirmVerification(payload: {
  item: string
  result: ClientVerificationResult
  notes?: string
  documentId?: string
}): Promise<void> {
  if (!client.value) return
  isVerificationSaving.value = true
  try {
    await clientStore.createVerification(client.value.id, payload)
    toastStore.show('success', 'Verification recorded', `"${payload.item}" marked as ${payload.result}.`)
    isVerificationDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to record verification', detail)
  } finally {
    isVerificationSaving.value = false
  }
}

async function handleConfirmEdit(payload: ClientEditForm): Promise<void> {
  if (!client.value) return
  isEditSaving.value = true
  try {
    const isIndividual = client.value.clientType === 'Individual'
    await clientStore.updateClient(client.value.id, {
      contactPerson: payload.contactPerson,
      mobile: payload.mobile,
      email: payload.email,
      city: payload.city,
      individualProfile: isIndividual
        ? {
            fullLegalName: payload.individualProfile.fullLegalName,
            preferredName: payload.individualProfile.preferredName || undefined,
            nationality: payload.individualProfile.nationality,
            dateOfBirth: payload.individualProfile.dateOfBirth,
            countryOfResidence: payload.individualProfile.countryOfResidence,
          }
        : undefined,
      organisationProfile: !isIndividual
        ? {
            legalName: payload.organisationProfile.legalName,
            tradeName: payload.organisationProfile.tradeName || undefined,
            organisationType: payload.organisationProfile.organisationType,
            registrationNumber: payload.organisationProfile.registrationNumber,
            tradeLicenceNumber: payload.organisationProfile.tradeLicenceNumber || undefined,
            taxIdentificationNumber: payload.organisationProfile.taxIdentificationNumber || undefined,
            countryOfRegistration: payload.organisationProfile.countryOfRegistration,
            dateOfIncorporation: payload.organisationProfile.dateOfIncorporation,
            website: payload.organisationProfile.website || undefined,
          }
        : undefined,
    })
    toastStore.show('success', 'Client updated', 'Changes were saved successfully.')
    isEditDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to update client', detail)
  } finally {
    isEditSaving.value = false
  }
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
      <ClientHeader :client="client" @edit="isEditDialogOpen = true" />

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
            :has-complete-profile="hasCompleteProfile"
          />
          <ClientOnboardingActions
            :client="client"
            :documents="clientStore.documents"
            :verifications="clientStore.verifications"
            :has-complete-profile="hasCompleteProfile"
            :loading="isOnboardingStateSaving"
            @advance="handleAdvanceOnboarding"
            @change-status="isStatusDialogOpen = true"
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

      <template v-else-if="activeTab === 'identification'">
        <ClientIdentificationList :identifications="clientStore.identifications" />
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
          <ClientDocumentCard
            v-for="document in clientStore.documents"
            :key="document.id"
            :document="document"
            @download="handleDocumentDownload(document)"
            @verify="openVerificationDialog(document)"
          />
        </div>
        <ClientDocumentUploadDialog v-model="isUploadDialogOpen" @upload="handleDocumentUpload" />
      </template>

      <template v-else-if="activeTab === 'verification'">
        <div class="flex items-center justify-end">
          <BaseButton size="sm" :icon="ShieldCheck" @click="openVerificationDialog()">Record Verification</BaseButton>
        </div>
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

      <ClientOnboardingStatusDialog
        v-model="isStatusDialogOpen"
        :current-state="client.onboardingState"
        :loading="isOnboardingStateSaving"
        @confirm="handleConfirmStatusChange"
      />
      <ClientVerificationDialog
        v-model="isVerificationDialogOpen"
        :initial-item="verificationDialogTarget?.title"
        :document-id="verificationDialogTarget?.id"
        :loading="isVerificationSaving"
        @confirm="handleConfirmVerification"
      />
      <ClientEditDialog
        v-model="isEditDialogOpen"
        :client="client"
        :loading="isEditSaving"
        @confirm="handleConfirmEdit"
      />
    </template>
  </div>
</template>
