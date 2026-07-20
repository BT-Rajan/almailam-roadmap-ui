import { CLIENT_ADDRESSES } from '@/mock/clientAddresses'
import { CLIENT_AUDIT_EVENTS } from '@/mock/clientAuditEvents'
import { CLIENT_CONSENTS } from '@/mock/clientConsents'
import { CLIENT_CONTACTS } from '@/mock/clientContacts'
import { CLIENT_DOCUMENTS } from '@/mock/clientDocuments'
import { CLIENT_IDENTIFICATIONS } from '@/mock/clientIdentifications'
import { CLIENT_VERIFICATIONS } from '@/mock/clientVerifications'
import { CLIENTS } from '@/mock/clients'
import type {
  Client,
  ClientAddress,
  ClientAuditEvent,
  ClientConsent,
  ClientContact,
  ClientDocument,
  ClientDuplicateMatch,
  ClientIdentification,
  ClientVerification,
} from '@/types/Client'
import { simulateNetworkDelay } from '@/utils/mockDelay'

async function getClients(): Promise<Client[]> {
  await simulateNetworkDelay()
  return [...CLIENTS]
}

async function getClientById(clientId: string): Promise<Client | undefined> {
  await simulateNetworkDelay()
  return CLIENTS.find((client) => client.id === clientId)
}

async function getContactsForClient(clientId: string): Promise<ClientContact[]> {
  await simulateNetworkDelay(200)
  return CLIENT_CONTACTS.filter((contact) => contact.clientId === clientId)
}

async function getAddressesForClient(clientId: string): Promise<ClientAddress[]> {
  await simulateNetworkDelay(200)
  return CLIENT_ADDRESSES.filter((address) => address.clientId === clientId)
}

async function getIdentificationsForClient(clientId: string): Promise<ClientIdentification[]> {
  await simulateNetworkDelay(200)
  return CLIENT_IDENTIFICATIONS.filter((identification) => identification.clientId === clientId)
}

async function getDocumentsForClient(clientId: string): Promise<ClientDocument[]> {
  await simulateNetworkDelay(200)
  return CLIENT_DOCUMENTS.filter((document) => document.clientId === clientId)
}

async function getVerificationsForClient(clientId: string): Promise<ClientVerification[]> {
  await simulateNetworkDelay(200)
  return CLIENT_VERIFICATIONS.filter((verification) => verification.clientId === clientId)
}

async function getConsentsForClient(clientId: string): Promise<ClientConsent[]> {
  await simulateNetworkDelay(200)
  return CLIENT_CONSENTS.filter((consent) => consent.clientId === clientId)
}

async function getAuditEventsForClient(clientId: string): Promise<ClientAuditEvent[]> {
  await simulateNetworkDelay(200)
  return CLIENT_AUDIT_EVENTS.filter((event) => event.clientId === clientId).sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
  )
}

/**
 * Looks for existing clients that share a name, mobile number or email with the
 * supplied values, so the onboarding wizard can warn about possible duplicates
 * before a new client record is confirmed.
 */
async function findPossibleDuplicates(name: string, mobile: string, email: string): Promise<ClientDuplicateMatch[]> {
  await simulateNetworkDelay(250)

  const normalisedName = name.trim().toLowerCase()
  const normalisedMobile = mobile.replace(/\D/g, '')
  const normalisedEmail = email.trim().toLowerCase()

  const matches: ClientDuplicateMatch[] = []

  CLIENTS.forEach((client) => {
    const matchedOn: string[] = []

    if (normalisedName.length > 2 && client.companyName.toLowerCase().includes(normalisedName)) {
      matchedOn.push('Name')
    }
    if (normalisedMobile.length >= 7 && client.mobile.replace(/\D/g, '') === normalisedMobile) {
      matchedOn.push('Mobile number')
    }
    if (normalisedEmail.length > 3 && client.email.toLowerCase() === normalisedEmail) {
      matchedOn.push('Email')
    }

    if (matchedOn.length > 0) {
      matches.push({ client, matchedOn })
    }
  })

  return matches
}

export const clientService = {
  getClients,
  getClientById,
  getContactsForClient,
  getAddressesForClient,
  getIdentificationsForClient,
  getDocumentsForClient,
  getVerificationsForClient,
  getConsentsForClient,
  getAuditEventsForClient,
  findPossibleDuplicates,
}
