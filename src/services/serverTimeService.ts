import { apiClient } from '@/services/httpClient'
import type { ServerTime } from '@/types/ServerTime'

async function getServerTime(): Promise<ServerTime> {
  return apiClient.get<ServerTime>('/api/server-time')
}

export const serverTimeService = { getServerTime }
