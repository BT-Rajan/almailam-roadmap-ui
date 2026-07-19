import { CLIENTS } from '@/mock/clients'
import type { Client } from '@/types/Client'
import { simulateNetworkDelay } from '@/utils/mockDelay'

async function getClients(): Promise<Client[]> {
  await simulateNetworkDelay()
  return [...CLIENTS]
}

async function getClientById(clientId: string): Promise<Client | undefined> {
  await simulateNetworkDelay()
  return CLIENTS.find((client) => client.id === clientId)
}

export const clientService = {
  getClients,
  getClientById,
}
