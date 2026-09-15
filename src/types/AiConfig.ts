export type AIProviderId = 'claude' | 'deepseek'

export type AIConnectionStatus = 'connected' | 'not-configured' | 'error'

export interface AIProviderConfig {
  id: AIProviderId
  label: string
  model: string
  apiKeyMasked: string
  // True specifically when a key was saved but no longer decrypts (e.g.
  // the server's encryption key rotated since) -- distinct from never
  // having had one entered. Without checking this, apiKeyMasked keeps
  // showing what looks like a normal saved key at the same time status
  // says not-configured, with nothing explaining the contradiction.
  keyUnreadable: boolean
  status: AIConnectionStatus
  // Write-only, local-only: a raw key just typed into the admin form,
  // staged until Save Changes is clicked. Never present in a GET response
  // -- the server never echoes back a real key. Cleared after a
  // successful save (see aiConfigStore.saveConfiguration).
  apiKey?: string
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
  kbDefaultSystemPrompt: string
  kbMaxUploadSizeMb: number
  kbMaxDocumentChars: number
  kbMaxContextChars: number
  providers: AIProviderConfig[]
}

export interface ProviderTestResult {
  success: boolean
  message: string
}
