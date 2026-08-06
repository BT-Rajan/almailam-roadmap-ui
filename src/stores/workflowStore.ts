import { defineStore } from 'pinia'

import { workflowService } from '@/services/workflowService'
import type { WorkflowStageConfig, WorkflowTemplate } from '@/types/Workflow'

interface WorkflowStoreState {
  templates: WorkflowTemplate[]
  selectedTemplateId: string | undefined
  isLoading: boolean
  error: string | undefined
  isMutating: boolean
  mutationError: string | undefined
}

export const useWorkflowStore = defineStore('workflow', {
  state: (): WorkflowStoreState => ({
    templates: [],
    selectedTemplateId: undefined,
    isLoading: false,
    error: undefined,
    isMutating: false,
    mutationError: undefined,
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

    async addStage(name: string, description: string) {
      const template = this.selectedTemplate
      if (!template) return
      this.isMutating = true
      this.mutationError = undefined
      try {
        const stage = await workflowService.addStage(template.id, name, description)
        template.stages = [...template.stages, stage]
      } catch {
        this.mutationError = 'Unable to add the stage. Please try again.'
      } finally {
        this.isMutating = false
      }
    },

    async updateStage(stageId: string, fields: Partial<Pick<WorkflowStageConfig, 'name' | 'description'>>) {
      const template = this.selectedTemplate
      if (!template) return
      this.isMutating = true
      this.mutationError = undefined
      try {
        const updated = await workflowService.updateStage(stageId, fields)
        template.stages = template.stages.map((stage) => (stage.id === stageId ? updated : stage))
      } catch {
        this.mutationError = 'Unable to update the stage. Please try again.'
      } finally {
        this.isMutating = false
      }
    },

    async removeStage(stageId: string) {
      const template = this.selectedTemplate
      if (!template) return
      this.isMutating = true
      this.mutationError = undefined
      try {
        await workflowService.removeStage(stageId)
        template.stages = template.stages.filter((stage) => stage.id !== stageId)
      } catch {
        this.mutationError = 'Unable to remove the stage. Please try again.'
      } finally {
        this.isMutating = false
      }
    },

    async moveStage(stageId: string, direction: 'up' | 'down') {
      const template = this.selectedTemplate
      if (!template) return
      this.isMutating = true
      this.mutationError = undefined
      try {
        template.stages = await workflowService.moveStage(stageId, direction)
      } catch {
        this.mutationError = 'Unable to reorder the stages. Please try again.'
      } finally {
        this.isMutating = false
      }
    },

    async setDefaultTemplate(templateId: string) {
      this.isMutating = true
      this.mutationError = undefined
      try {
        this.templates = await workflowService.setDefaultTemplate(templateId)
      } catch {
        this.mutationError = 'Unable to change the default workflow. Please try again.'
      } finally {
        this.isMutating = false
      }
    },
  },
})
