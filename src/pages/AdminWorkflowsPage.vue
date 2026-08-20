<script setup lang="ts">
import { computed, onMounted } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import Stepper from '@/components/common/Stepper.vue'
import WorkflowCard from '@/components/administration/WorkflowCard.vue'
import WorkflowStageEditor from '@/components/administration/WorkflowStageEditor.vue'
import { useToastStore } from '@/stores/toastStore'
import { useWorkflowStore } from '@/stores/workflowStore'

const workflowStore = useWorkflowStore()
const toastStore = useToastStore()

const stepperSteps = computed(() => (workflowStore.selectedTemplate?.stages ?? []).map((stage) => ({ label: stage.name })))

function loadData(): void {
  workflowStore.loadTemplates()
}

onMounted(() => {
  if (workflowStore.templates.length === 0) loadData()
})

function handleSetDefault(): void {
  if (!workflowStore.selectedTemplate) return
  const name = workflowStore.selectedTemplate.name
  workflowStore.setDefaultTemplate(workflowStore.selectedTemplate.id).then(() => {
    if (workflowStore.mutationError) {
      toastStore.show('error', 'Unable to change default', workflowStore.mutationError)
    } else {
      toastStore.show('info', 'Default workflow changed', `${name} is now the default.`)
    }
  })
}

// Stage edits save immediately as they're made (see workflowStore), so the
// only feedback needed here is a toast if a particular edit failed to save.
function reportIfFailed(action: Promise<void>): void {
  action.then(() => {
    if (workflowStore.mutationError) {
      toastStore.show('error', 'Change not saved', workflowStore.mutationError)
    }
  })
}

function handleUpdateStage(stageId: string, fields: Parameters<typeof workflowStore.updateStage>[1]): void {
  reportIfFailed(workflowStore.updateStage(stageId, fields))
}

function handleRemoveStage(stageId: string): void {
  reportIfFailed(workflowStore.removeStage(stageId))
}

function handleMoveStage(stageId: string, direction: 'up' | 'down'): void {
  reportIfFailed(workflowStore.moveStage(stageId, direction))
}

function handleAddStage(name: string, description: string): void {
  reportIfFailed(workflowStore.addStage(name, description))
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader title="Workflow Configuration" subtitle="Define and adjust the project workflow stages." />

    <ErrorState v-if="workflowStore.error" :description="workflowStore.error" @retry="loadData" />

    <div v-else-if="workflowStore.isLoading" class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <div class="rounded-xl border border-border-light bg-bg-card p-6">
        <SkeletonLoader :rows="5" />
      </div>
      <div class="rounded-xl border border-border-light bg-bg-card p-6 laptop:col-span-2">
        <SkeletonLoader :rows="8" />
      </div>
    </div>

    <div v-else class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <div class="flex flex-col gap-3">
        <WorkflowCard
          v-for="template in workflowStore.templates"
          :key="template.id"
          :template="template"
          :active="template.id === workflowStore.selectedTemplateId"
          @select="workflowStore.selectTemplate"
        />
      </div>

      <div class="flex flex-col gap-6 laptop:col-span-2">
        <EmptyState v-if="!workflowStore.selectedTemplate" title="Select a workflow template" description="Choose a template on the left to view and edit its stages." />

        <template v-else>
          <Card>
            <template #header>
              <h3 class="text-sm font-semibold text-text-primary">Workflow Visualization</h3>
            </template>
            <div class="overflow-x-auto pb-1">
              <div class="min-w-[640px]">
                <Stepper :steps="stepperSteps" :current-step="-1" />
              </div>
            </div>
          </Card>

          <Card>
            <template #header>
              <div class="flex items-center justify-between gap-3">
                <h3 class="text-sm font-semibold text-text-primary">{{ workflowStore.selectedTemplate.name }} Stages</h3>
                <div class="flex items-center gap-2">
                  <BaseButton
                    v-if="!workflowStore.selectedTemplate.isDefault"
                    variant="secondary"
                    size="sm"
                    @click="handleSetDefault"
                  >
                    Set as Default
                  </BaseButton>
                </div>
              </div>
            </template>

            <WorkflowStageEditor
              :stages="workflowStore.selectedTemplate.stages"
              @update="handleUpdateStage"
              @remove="handleRemoveStage"
              @move="handleMoveStage"
              @add="handleAddStage"
            />
          </Card>
        </template>
      </div>
    </div>
  </div>
</template>
