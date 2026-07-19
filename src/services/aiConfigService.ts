import { AI_CONFIGURATION } from '@/mock/aiConfiguration'
import { PROMPT_TEMPLATES } from '@/mock/promptTemplates'
import type { AIConfiguration, AIProviderId, PromptTemplate, ProviderTestResult } from '@/types/AiConfig'
import { simulateNetworkDelay } from '@/utils/mockDelay'

const CONNECTION_TEST_DELAY_MS = 1200

async function getConfiguration(): Promise<AIConfiguration> {
  await simulateNetworkDelay()
  return { ...AI_CONFIGURATION, providers: AI_CONFIGURATION.providers.map((provider) => ({ ...provider })) }
}

async function saveConfiguration(config: AIConfiguration): Promise<AIConfiguration> {
  await simulateNetworkDelay()
  return { ...config, providers: config.providers.map((provider) => ({ ...provider })) }
}

async function testProviderConnection(providerId: AIProviderId): Promise<ProviderTestResult> {
  await simulateNetworkDelay(CONNECTION_TEST_DELAY_MS)

  const provider = AI_CONFIGURATION.providers.find((item) => item.id === providerId)
  if (!provider || !provider.apiKeyMasked) {
    return { success: false, message: 'No API key configured for this provider.' }
  }

  return { success: true, message: `Connected to ${provider.label} successfully.` }
}

async function getPromptTemplates(): Promise<PromptTemplate[]> {
  await simulateNetworkDelay()
  return [...PROMPT_TEMPLATES]
}

async function savePromptTemplate(templateId: string, input: Omit<PromptTemplate, 'id'>): Promise<PromptTemplate> {
  await simulateNetworkDelay()
  const index = PROMPT_TEMPLATES.findIndex((template) => template.id === templateId)
  if (index === -1) throw new Error(`Prompt template ${templateId} not found`)
  PROMPT_TEMPLATES[index] = { ...input, id: templateId }
  return PROMPT_TEMPLATES[index]
}

export const aiConfigService = {
  getConfiguration,
  saveConfiguration,
  testProviderConnection,
  getPromptTemplates,
  savePromptTemplate,
}
