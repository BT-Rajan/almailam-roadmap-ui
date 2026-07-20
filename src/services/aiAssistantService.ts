import { ASSISTANT_RESPONSE_POOL } from '@/mock/aiAssistantResponses'
import type { AIProviderId } from '@/types/AiConfig'
import type { AIInteraction } from '@/types/AiAssistant'
import { simulateNetworkDelay } from '@/utils/mockDelay'

const AI_THINKING_DELAY_MS = 1100

let responseCounter = 0

function truncate(text: string, maxLength: number): string {
  return text.length > maxLength ? `${text.slice(0, maxLength).trim()}…` : text
}

async function getResponse(prompt: string, provider: AIProviderId, templateName?: string): Promise<AIInteraction> {
  await simulateNetworkDelay(AI_THINKING_DELAY_MS)

  const pooled = ASSISTANT_RESPONSE_POOL[responseCounter % ASSISTANT_RESPONSE_POOL.length]
  responseCounter += 1

  return {
    id: crypto.randomUUID(),
    prompt,
    templateName,
    provider,
    summary: `Here's a summary for: "${truncate(prompt, 80)}"`,
    details: pooled.details,
    confidence: pooled.confidence,
    suggestedActions: pooled.suggestedActions,
    timestamp: new Date().toISOString(),
  }
}

export const aiAssistantService = {
  getResponse,
}
