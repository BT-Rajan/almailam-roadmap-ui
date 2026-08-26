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
  kbSystemPrompt: string
  kbMaxUploadSizeMb: number
  kbMaxDocumentChars: number
  kbMaxContextChars: number
  providers: AIProviderConfig[]
}

export interface ProviderTestResult {
  success: boolean
  message: string
}
