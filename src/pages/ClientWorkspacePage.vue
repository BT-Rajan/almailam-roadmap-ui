<script setup lang="ts">
import { FilePlus, MessageSquare, Plus, UserPlus, MapPinPlus, IdCardLanyard } from '@lucide/vue'
import { computed, defineAsyncComponent, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Alert from '@/components/common/Alert.vue'
import Card from '@/components/common/Card.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import DetailPanel from '@/components/common/DetailPanel.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import ClientAddressCard from '@/components/client/ClientAddressCard.vue'
import ClientAddressEditDialog from '@/components/client/ClientAddressEditDialog.vue'
import ClientContactEditDialog from '@/components/client/ClientContactEditDialog.vue'
import ClientEditDialog from '@/components/client/ClientEditDialog.vue'
import ClientHeader from '@/components/client/ClientHeader.vue'
import ClientMergeDialog from '@/components/client/ClientMergeDialog.vue'
import ClientIdentificationEditDialog from '@/components/client/ClientIdentificationEditDialog.vue'
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
const ClientDocumentEditDialog = defineAsyncComponent(() => import('@/components/client/ClientDocumentEditDialog.vue'))
const ClientDocumentVersionDialog = defineAsyncComponent(() => import('@/components/client/ClientDocumentVersionDialog.vue'))
const ClientVerificationDialog = defineAsyncComponent(() => import('@/components/client/ClientVerificationDialog.vue'))
const ClientAuditTrail = defineAsyncComponent(() => import('@/components/client/ClientAuditTrail.vue'))
const ProjectCard = defineAsyncComponent(() => import('@/components/project/ProjectCard.vue'))
import { useClientStore } from '@/stores/clientStore'
import { useProjectStore } from '@/stores/projectStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type {
  ClientAddress,
  ClientContact,
  ClientDocument,
  ClientDocumentCategory,
  ClientDocumentVersion,
  ClientDuplicateMatch,
  ClientIdentification,
  ClientOnboardingState,
  ClientVerificationResult,
  ClientWorkspaceTab,
  ClientWorkspaceTabKey,
} from '@/types/Client'
import type { ClientEditForm } from '@/utils/clientValidation'
import { getClientDisplayName } from '@/utils/clientHelpers'
import { formatDate } from '@/utils/dateFormatter'

const route = useRoute()
const router = useRouter()
const clientStore = useClientStore()
const projectStore = useProjectStore()
const resultDialogStore = useResultDialogStore()

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
const isStatusToggleSaving = ref(false)
const isDeleteClientDialogOpen = ref(false)
const isDeleteClientSaving = ref(false)
const identificationDuplicates = ref<ClientDuplicateMatch[]>([])
const isMergeDialogOpen = ref(false)
const isMergeSaving = ref(false)
const mergeDialogMatch = ref<ClientDuplicateMatch | null>(null)

// Contact/address/identification/document edit-or-add dialogs: a null
// target means "adding new"; a non-null target means "editing this one".
const isContactDialogOpen = ref(false)
const isContactSaving = ref(false)
const contactDialogTarget = ref<ClientContact | null>(null)

const isAddressDialogOpen = ref(false)
const isAddressSaving = ref(false)
const addressDialogTarget = ref<ClientAddress | null>(null)

const isIdentificationDialogOpen = ref(false)
const isIdentificationSaving = ref(false)
const identificationDialogTarget = ref<ClientIdentification | null>(null)

const isDocumentEditDialogOpen = ref(false)
const isDocumentEditSaving = ref(false)
const documentEditTarget = ref<ClientDocument | null>(null)

// One shared delete-confirmation dialog for all four record types, rather
// than four near-identical ConfirmationDialog instances.
type DeletableRecordType = 'contact' | 'address' | 'identification' | 'document'
const isDeleteDialogOpen = ref(false)
const isDeleteSaving = ref(false)
const deleteTarget = ref<{ type: DeletableRecordType; id: string; label: string } | null>(null)

const TABS: ClientWorkspaceTab[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'contacts', label: 'Contacts' },
  { key: 'identification', label: 'Identification' },
  { key: 'documents', label: 'Documents' },
  { key: 'projects', label: 'Projects' },
  { key: 'activity', label: 'Activity' },
]

const client = computed(() => clientStore.getClientById(clientId.value))
const clientProjects = computed(() => projectStore.projects.filter((project) => project.clientId === clientId.value))
// Same eligibility rule NewProjectWizardPage.vue and the backend both
// enforce (onboardingState === 'Ready' && status === 'Active') --
// mirrored here so this button never leads to a dead end where the
// client silently isn't selectable on the next page.
const clientEligibleForNewProject = computed(
  () => client.value?.onboardingState === 'Ready' && client.value?.status === 'Active',
)

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
    { label: 'Account Manager', value: client.value.accountManagerName ?? 'Unassigned' },
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
  // Cheap, targeted check (only scans this client's own identification
  // numbers against others), unlike the free-text onboarding-wizard
  // duplicate check -- safe to run automatically on every workspace visit.
  try {
    identificationDuplicates.value = await clientStore.findIdentificationDuplicates(clientId.value)
  } catch {
    identificationDuplicates.value = []
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
    resultDialogStore.showSuccess('Document added', `${payload.title} was uploaded successfully.`)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to upload document', detail)
  }
}

async function handleDocumentDownload(document: ClientDocument): Promise<void> {
  if (!client.value) return
  try {
    await clientStore.downloadDocument(client.value.id, document.id, document.originalFilename)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to download document', detail)
  }
}

async function handleViewIdentificationDocument(document: ClientDocument): Promise<void> {
  if (!client.value) return
  try {
    await clientStore.viewDocument(client.value.id, document.id)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to open document', detail)
  }
}

async function handleReplaceDocumentFile(document: ClientDocument, file: File): Promise<void> {
  if (!client.value) return
  try {
    await clientStore.replaceDocumentFile(client.value.id, document.id, file)
    resultDialogStore.showSuccess('File replaced', `${document.title} was updated to a new version.`)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to replace file', detail)
  }
}

const isVersionHistoryOpen = ref(false)
const isVersionHistoryLoading = ref(false)
const versionHistoryDocument = ref<ClientDocument | undefined>(undefined)

async function openVersionHistory(document: ClientDocument): Promise<void> {
  if (!client.value) return
  versionHistoryDocument.value = document
  isVersionHistoryOpen.value = true
  isVersionHistoryLoading.value = true
  try {
    await clientStore.loadDocumentVersions(client.value.id, document.id)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to load version history', detail)
  } finally {
    isVersionHistoryLoading.value = false
  }
}

async function handleDownloadVersion(version: ClientDocumentVersion): Promise<void> {
  if (!client.value || !versionHistoryDocument.value) return
  try {
    await clientStore.downloadDocumentVersion(client.value.id, versionHistoryDocument.value.id, version.id, version.originalFilename)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to download version', detail)
  }
}

async function applyOnboardingState(nextState: ClientOnboardingState, reason?: string): Promise<void> {
  if (!client.value) return
  isOnboardingStateSaving.value = true
  try {
    await clientStore.setOnboardingState(client.value.id, nextState, reason)
    resultDialogStore.showSuccess('Onboarding status updated', `Status changed to "${nextState}".`)
    isStatusDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to update onboarding status', detail)
  } finally {
    isOnboardingStateSaving.value = false
  }
}

async function handleAutoAdvanceOnboarding(): Promise<void> {
  if (!client.value) return
  isOnboardingStateSaving.value = true
  try {
    const before = client.value.onboardingState
    const updated = await clientStore.autoAdvanceOnboarding(client.value.id)
    resultDialogStore.showSuccess(
      'Onboarding status updated',
      updated.onboardingState === before
        ? 'This client is already at a status that needs a manual decision -- use Change Status.'
        : `Status advanced from "${before}" to "${updated.onboardingState}".`,
    )
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to advance onboarding status', detail)
  } finally {
    isOnboardingStateSaving.value = false
  }
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
    resultDialogStore.showSuccess('Verification recorded', `"${payload.item}" marked as ${payload.result}.`)
    isVerificationDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to record verification', detail)
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
      accountManagerId: payload.accountManagerId,
      notes: payload.notes,
      communicationPreference: {
        preferredLanguage: payload.preferredLanguage,
        preferredChannel: payload.preferredChannel,
      },
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
    resultDialogStore.showSuccess('Client updated', 'Changes were saved successfully.')
    isEditDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to update client', detail)
  } finally {
    isEditSaving.value = false
  }
}

async function handleToggleStatus(): Promise<void> {
  if (!client.value) return
  const nextStatus = client.value.status === 'Active' ? 'Inactive' : 'Active'
  isStatusToggleSaving.value = true
  try {
    await clientStore.setClientStatus(client.value.id, nextStatus)
    resultDialogStore.showSuccess('Status updated', `Client marked as ${nextStatus}.`)
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to update status', detail)
  } finally {
    isStatusToggleSaving.value = false
  }
}

async function handleConfirmDeleteClient(): Promise<void> {
  if (!client.value) return
  isDeleteClientSaving.value = true
  try {
    await clientStore.deleteClient(client.value.id)
    resultDialogStore.showSuccess('Client deleted', `${client.value.companyName} was removed.`)
    isDeleteClientDialogOpen.value = false
    router.push({ name: ROUTE_NAMES.CLIENTS })
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to delete client', detail)
  } finally {
    isDeleteClientSaving.value = false
  }
}

function openMergeDialog(match: ClientDuplicateMatch): void {
  mergeDialogMatch.value = match
  isMergeDialogOpen.value = true
}

async function handleConfirmMerge(direction: 'keep-current' | 'keep-other'): Promise<void> {
  if (!client.value || !mergeDialogMatch.value) return
  const targetId = direction === 'keep-current' ? client.value.id : mergeDialogMatch.value.client.id
  const sourceId = direction === 'keep-current' ? mergeDialogMatch.value.client.id : client.value.id
  const keptName = direction === 'keep-current' ? client.value.companyName : mergeDialogMatch.value.client.companyName

  isMergeSaving.value = true
  try {
    await clientStore.mergeClients(targetId, sourceId)
    resultDialogStore.showSuccess('Clients merged', `Merged into ${keptName}.`)
    isMergeDialogOpen.value = false
    if (targetId !== client.value.id) {
      // The record being VIEWED was the one merged away -- navigate to
      // the surviving record instead of showing a now-deleted client.
      router.push({ name: ROUTE_NAMES.CLIENT_WORKSPACE, params: { clientId: targetId } })
    }
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to merge clients', detail)
  } finally {
    isMergeSaving.value = false
  }
}

// --- Contacts ---

function openContactDialog(contact?: ClientContact): void {
  contactDialogTarget.value = contact ?? null
  isContactDialogOpen.value = true
}

async function handleConfirmContact(payload: {
  name: string
  contactType: ClientContact['contactType']
  mobile: string
  email: string
  isAuthorisedRepresentative: boolean
}): Promise<void> {
  if (!client.value) return
  isContactSaving.value = true
  try {
    if (contactDialogTarget.value) {
      await clientStore.updateContact(client.value.id, contactDialogTarget.value.id, payload)
      resultDialogStore.showSuccess('Contact updated', `${payload.name} was updated.`)
    } else {
      await clientStore.createContact(client.value.id, payload)
      resultDialogStore.showSuccess('Contact added', `${payload.name} was added.`)
    }
    isContactDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError(contactDialogTarget.value ? 'Failed to update contact' : 'Failed to add contact', detail)
  } finally {
    isContactSaving.value = false
  }
}

// --- Addresses ---

function openAddressDialog(address?: ClientAddress): void {
  addressDialogTarget.value = address ?? null
  isAddressDialogOpen.value = true
}

async function handleConfirmAddress(payload: {
  addressType: ClientAddress['addressType']
  country: string
  state: string
  city: string
  area: string
  street: string
  building: string
}): Promise<void> {
  if (!client.value) return
  isAddressSaving.value = true
  try {
    const normalised = {
      ...payload,
      area: payload.area || undefined,
      street: payload.street || undefined,
      building: payload.building || undefined,
    }
    if (addressDialogTarget.value) {
      await clientStore.updateAddress(client.value.id, addressDialogTarget.value.id, normalised)
      resultDialogStore.showSuccess('Address updated', 'The address was updated.')
    } else {
      await clientStore.createAddress(client.value.id, normalised)
      resultDialogStore.showSuccess('Address added', 'The address was added.')
    }
    isAddressDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError(addressDialogTarget.value ? 'Failed to update address' : 'Failed to add address', detail)
  } finally {
    isAddressSaving.value = false
  }
}

// --- Identification ---

function openIdentificationDialog(identification?: ClientIdentification): void {
  identificationDialogTarget.value = identification ?? null
  isIdentificationDialogOpen.value = true
}

async function handleConfirmIdentification(payload: {
  documentType: ClientIdentification['documentType']
  documentNumber: string
  issueDate: string
  expiryDate: string
  issuingCountry: string
}): Promise<void> {
  if (!client.value) return
  isIdentificationSaving.value = true
  try {
    if (identificationDialogTarget.value) {
      await clientStore.updateIdentification(client.value.id, identificationDialogTarget.value.id, payload)
      resultDialogStore.showSuccess('Identification updated', `${payload.documentType} was updated.`)
    } else {
      await clientStore.createIdentification(client.value.id, payload)
      resultDialogStore.showSuccess('Identification added', `${payload.documentType} was added.`)
    }
    isIdentificationDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError(identificationDialogTarget.value ? 'Failed to update identification' : 'Failed to add identification', detail)
  } finally {
    isIdentificationSaving.value = false
  }
}

// --- Document metadata edit ---

function openDocumentEditDialog(document: ClientDocument): void {
  documentEditTarget.value = document
  isDocumentEditDialogOpen.value = true
}

async function handleConfirmDocumentEdit(payload: {
  category: ClientDocumentCategory
  title: string
  issueDate: string
  expiryDate: string
  issuingAuthority: string
}): Promise<void> {
  if (!client.value || !documentEditTarget.value) return
  isDocumentEditSaving.value = true
  try {
    await clientStore.updateDocument(client.value.id, documentEditTarget.value.id, {
      category: payload.category,
      title: payload.title,
      issueDate: payload.issueDate || undefined,
      expiryDate: payload.expiryDate || undefined,
      issuingAuthority: payload.issuingAuthority || undefined,
    })
    resultDialogStore.showSuccess('Document updated', `${payload.title} was updated.`)
    isDocumentEditDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to update document', detail)
  } finally {
    isDocumentEditSaving.value = false
  }
}

// --- Shared delete confirmation ---

function requestDelete(type: DeletableRecordType, id: string, label: string): void {
  deleteTarget.value = { type, id, label }
  isDeleteDialogOpen.value = true
}

async function handleConfirmDelete(): Promise<void> {
  if (!client.value || !deleteTarget.value) return
  const { type, id, label } = deleteTarget.value
  isDeleteSaving.value = true
  try {
    if (type === 'contact') await clientStore.deleteContact(client.value.id, id)
    else if (type === 'address') await clientStore.deleteAddress(client.value.id, id)
    else if (type === 'identification') await clientStore.deleteIdentification(client.value.id, id)
    else await clientStore.deleteDocument(client.value.id, id)
    resultDialogStore.showSuccess('Removed', `${label} was removed.`)
    isDeleteDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to remove', detail)
  } finally {
    isDeleteSaving.value = false
  }
}

function openProject(projectId: string): void {
  router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId } })
}

function createProjectForClient(): void {
  router.push({ name: ROUTE_NAMES.PROJECT_NEW, query: { clientId: clientId.value } })
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
      <ClientHeader
        :client="client"
        :status-saving="isStatusToggleSaving"
        @edit="isEditDialogOpen = true"
        @toggle-status="handleToggleStatus"
        @delete="isDeleteClientDialogOpen = true"
      />

      <div v-if="identificationDuplicates.length > 0" class="flex flex-col gap-2">
        <Alert
          v-for="match in identificationDuplicates"
          :key="match.client.id"
          variant="warning"
          title="Possible duplicate client found"
          :description="`This client shares the same ${match.matchedOn.join(', ')} as ${getClientDisplayName(match.client)} (${match.client.code}). If this is genuinely the same person or organisation, merge the two records.`"
        >
          <template #action>
            <BaseButton size="sm" variant="secondary" @click="openMergeDialog(match)">Review & Merge</BaseButton>
          </template>
        </Alert>
      </div>

      <ClientWorkspaceTabs :tabs="TABS" :active-tab="activeTab" @select="activeTab = $event" />

      <template v-if="activeTab === 'overview'">
        <div
          id="client-tabpanel-overview"
          role="tabpanel"
          aria-labelledby="client-tab-overview"
          tabindex="0"
          class="grid grid-cols-1 gap-6 laptop:grid-cols-2"
        >
          <DetailPanel title="Profile Information" :items="profileDetailItems" />
          <div class="flex flex-col gap-3">
            <DetailPanel title="Contact Details" :items="contactDetailItems" />
            <Card>
              <template #header>
                <h3 class="text-sm font-semibold text-text-primary">Internal Notes</h3>
              </template>
              <p class="whitespace-pre-wrap text-sm text-text-secondary">
                {{ client.notes || 'No internal notes have been added yet.' }}
              </p>
            </Card>
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
            :client="client"
            :documents="clientStore.documents"
            :contacts="clientStore.contacts"
            :addresses="clientStore.addresses"
            :identifications="clientStore.identifications"
          />
          <ClientOnboardingActions
            :client="client"
            :documents="clientStore.documents"
            :contacts="clientStore.contacts"
            :addresses="clientStore.addresses"
            :identifications="clientStore.identifications"
            :verifications="clientStore.verifications"
            :loading="isOnboardingStateSaving"
            @autoAdvance="handleAutoAdvanceOnboarding"
            @change-status="isStatusDialogOpen = true"
          />
          <div class="flex flex-col gap-4">
            <div class="flex items-center justify-between">
              <h3 class="text-sm font-semibold text-text-primary">Addresses</h3>
              <BaseButton variant="secondary" size="sm" :icon="MapPinPlus" @click="openAddressDialog()">Add Address</BaseButton>
            </div>
            <ClientAddressCard
              v-for="address in clientStore.addresses"
              :key="address.id"
              :address="address"
              @edit="openAddressDialog(address)"
              @delete="requestDelete('address', address.id, `${address.addressType} address`)"
            />
            <EmptyState
              v-if="clientStore.addresses.length === 0"
              title="No address on file"
              description="Add an address to complete this client's profile."
            />
          </div>
        </div>
      </template>

      <div
        v-else-if="activeTab === 'contacts'"
        id="client-tabpanel-contacts"
        role="tabpanel"
        aria-labelledby="client-tab-contacts"
        tabindex="0"
        class="flex flex-col gap-6"
      >
        <div class="flex items-center justify-end">
          <BaseButton size="sm" :icon="UserPlus" @click="openContactDialog()">Add Contact</BaseButton>
        </div>
        <ClientContactList
          :contacts="clientStore.contacts"
          @edit="openContactDialog"
          @delete="(contact) => requestDelete('contact', contact.id, contact.name)"
        />
      </div>

      <div
        v-else-if="activeTab === 'identification'"
        id="client-tabpanel-identification"
        role="tabpanel"
        aria-labelledby="client-tab-identification"
        tabindex="0"
        class="flex flex-col gap-6"
      >
        <div class="flex items-center justify-end">
          <BaseButton size="sm" :icon="IdCardLanyard" @click="openIdentificationDialog()">Add Identification</BaseButton>
        </div>
        <ClientIdentificationList
          :identifications="clientStore.identifications"
          :documents="clientStore.documents"
          @edit="openIdentificationDialog"
          @delete="(identification) => requestDelete('identification', identification.id, identification.documentType)"
          @view="handleViewIdentificationDocument"
        />
      </div>

      <div
        v-else-if="activeTab === 'documents'"
        id="client-tabpanel-documents"
        role="tabpanel"
        aria-labelledby="client-tab-documents"
        tabindex="0"
        class="flex flex-col gap-6"
      >
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
            @edit="openDocumentEditDialog(document)"
            @delete="requestDelete('document', document.id, document.title)"
            @history="openVersionHistory(document)"
            @replace-file="(file) => handleReplaceDocumentFile(document, file)"
          />
        </div>
        <ClientDocumentUploadDialog v-model="isUploadDialogOpen" @upload="handleDocumentUpload" />
        <ClientDocumentVersionDialog
          v-model="isVersionHistoryOpen"
          :document="versionHistoryDocument"
          :versions="clientStore.documentVersions"
          :loading="isVersionHistoryLoading"
          @download="handleDownloadVersion"
        />
      </div>

      <div
        v-else-if="activeTab === 'projects'"
        id="client-tabpanel-projects"
        role="tabpanel"
        aria-labelledby="client-tab-projects"
        tabindex="0"
      >
        <div class="mb-4 flex flex-col items-end gap-1 no-print">
          <BaseButton
            size="sm"
            :icon="Plus"
            :disabled="!clientEligibleForNewProject"
            @click="createProjectForClient"
          >
            New Project
          </BaseButton>
          <p v-if="!clientEligibleForNewProject" class="text-xs text-text-muted">
            Onboarding must be Ready and the client Active before a project can be created.
          </p>
        </div>
        <EmptyState
          v-if="clientProjects.length === 0"
          title="No projects yet"
          description="Projects created for this client will appear here."
          :action-label="clientEligibleForNewProject ? 'New Project' : undefined"
          @action="createProjectForClient"
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
      </div>

      <div
        v-else-if="activeTab === 'activity'"
        id="client-tabpanel-activity"
        role="tabpanel"
        aria-labelledby="client-tab-activity"
        tabindex="0"
      >
        <ClientAuditTrail :events="clientStore.auditEvents" />
      </div>


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
      <ClientContactEditDialog
        v-model="isContactDialogOpen"
        :contact="contactDialogTarget ?? undefined"
        :loading="isContactSaving"
        @confirm="handleConfirmContact"
      />
      <ClientAddressEditDialog
        v-model="isAddressDialogOpen"
        :address="addressDialogTarget ?? undefined"
        :loading="isAddressSaving"
        @confirm="handleConfirmAddress"
      />
      <ClientIdentificationEditDialog
        v-model="isIdentificationDialogOpen"
        :identification="identificationDialogTarget ?? undefined"
        :client-type="client.clientType"
        :loading="isIdentificationSaving"
        @confirm="handleConfirmIdentification"
      />
      <ClientDocumentEditDialog
        v-model="isDocumentEditDialogOpen"
        :document="documentEditTarget"
        :loading="isDocumentEditSaving"
        @confirm="handleConfirmDocumentEdit"
      />
      <ConfirmationDialog
        v-model="isDeleteDialogOpen"
        title="Remove record"
        :message="deleteTarget ? `Remove ${deleteTarget.label}? This cannot be undone from the app.` : ''"
        confirm-label="Remove"
        confirm-variant="danger"
        :loading="isDeleteSaving"
        @confirm="handleConfirmDelete"
      />
      <ConfirmationDialog
        v-if="client"
        v-model="isDeleteClientDialogOpen"
        title="Delete client"
        :message="`Delete ${client.companyName}? This cannot be undone from the app, and is blocked if the client has any projects on file.`"
        confirm-label="Delete"
        confirm-variant="danger"
        :loading="isDeleteClientSaving"
        @confirm="handleConfirmDeleteClient"
      />
      <ClientMergeDialog
        v-model="isMergeDialogOpen"
        :current-client="client"
        :match="mergeDialogMatch"
        :loading="isMergeSaving"
        @confirm="handleConfirmMerge"
      />
    </template>
  </div>
</template>
