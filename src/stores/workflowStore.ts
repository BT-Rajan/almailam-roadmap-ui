import { defineStore } from 'pinia'

import { workflowService } from '@/services/workflowService'
import type { WorkflowStageConfig, WorkflowTemplate } from '@/types/Workflow'

interface WorkflowStoreState {
  templates: WorkflowTemplate[]
  selectedTemplateId: string | undefined
  isLoading: boolean
  error: string | undefined
}

function generateStageId(): string {
  return `STG-${Date.now().toString(36).toUpperCase()}`
}

export const useWorkflowStore = defineStore('workflow', {
  state: (): WorkflowStoreState => ({
    templates: [],
    selectedTemplateId: undefined,
    isLoading: false,
    error: undefined,
  }),

  getters: {
    selectedTemplate(state): WorkflowTemplate | undefined {
      return state.templates.find((template) => template.id === state.selectedTemplateId)
    },
  },

  actions: {
    async loadTemplates() {
      this.isLoading = true
      this.error = undefined
      try {
        this.templates = await workflowService.getTemplates()
        if (!this.selectedTemplateId && this.templates.length > 0) {
          this.selectedTemplateId = this.templates[0]!.id
        }
      } catch {
        this.error = 'Unable to load workflow templates. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    selectTemplate(templateId: string) {
      this.selectedTemplateId = templateId
    },

    addStage(name: string, description: string) {
      const template = this.selectedTemplate
      if (!template) return
      const newStage: WorkflowStageConfig = { id: generateStageId(), name, description }
      template.stages = [...template.stages, newStage]
    },

    updateStage(stageId: string, fields: Partial<Pick<WorkflowStageConfig, 'name' | 'description'>>) {
      const template = this.selectedTemplate
      if (!template) return
      template.stages = template.stages.map((stage) => (stage.id === stageId ? { ...stage, ...fields } : stage))
    },

    removeStage(stageId: string) {
      const template = this.selectedTemplate
      if (!template) return
      template.stages = template.stages.filter((stage) => stage.id !== stageId)
    },

    moveStage(stageId: string, direction: 'up' | 'down') {
      const template = this.selectedTemplate
      if (!template) return
      const stages = [...template.stages]
      const index = stages.findIndex((stage) => stage.id === stageId)
      const targetIndex = direction === 'up' ? index - 1 : index + 1
      if (index === -1 || targetIndex < 0 || targetIndex >= stages.length) return

      const [moved] = stages.splice(index, 1)
      stages.splice(targetIndex, 0, moved!)
      template.stages = stages
    },

    setDefaultTemplate(templateId: string) {
      this.templates = this.templates.map((template) => ({ ...template, isDefault: template.id === templateId }))
    },
  },
})
