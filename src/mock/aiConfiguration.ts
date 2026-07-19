import type { AIConfiguration } from '@/types/AiConfig'

export const AI_CONFIGURATION: AIConfiguration = {
  isEnabled: true,
  defaultProvider: 'claude',
  providerPriority: ['claude', 'deepseek'],
  timeoutSeconds: 30,
  maxTokens: 2048,
  temperature: 0.4,
  cacheDurationMinutes: 60,
  retryLimit: 2,
  providers: [
    {
      id: 'claude',
      label: 'Claude (Anthropic)',
      model: 'claude-sonnet-4-6',
      apiKeyMasked: 'sk-ant-••••••••4f2a',
      status: 'connected',
    },
    {
      id: 'deepseek',
      label: 'DeepSeek',
      model: 'deepseek-chat',
      apiKeyMasked: '',
      status: 'not-configured',
    },
  ],
}
