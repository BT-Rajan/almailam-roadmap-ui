export type AIProviderId = 'claude' | 'deepseek'

export type AIConnectionStatus = 'connected' | 'not-configured' | 'error'

export interface AIProviderConfig {
  id: AIProviderId
  label: string
  model: string
  apiKeyMasked: string
  status: AIConnectionStatus
}

export interface AIConfiguration {
  isEnabled: boolean
  defaultProvider: AIProviderId
  providerPriority: AIProviderId[]
  timeoutSeconds: number
  maxTokens: number
  temperature: number
  cacheDurationMinutes: number
  retryLimit: number
  providers: AIProviderConfig[]
}

export type PromptTemplateModule =
  | 'Projects'
  | 'Documents'
  | 'Contracts'
  | 'Government Forms'
  | 'Customer Communication'
  | 'Reports'

export interface PromptTemplate {
  id: string
  name: string
  description: string
  module: PromptTemplateModule
  template: string
}

export interface ProviderTestResult {
  success: boolean
  message: string
}
