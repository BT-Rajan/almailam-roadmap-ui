// A named, admin-managed bundle of execution step templates -- e.g.
// "Standard Process", "Commercial Fit-out". A project is assigned one
// at creation and snapshots exactly that set's steps into its own
// checklist -- see ProjectExecutionStep below.
export interface ExecutionStepSet {
  id: string
  name: string
  description: string | null
}

export interface ExecutionStepTemplateItem {
  id: string
  stepSetId: string
  name: string
  sequenceNumber: number
  weightPercentage: number
  stageKey: string
  isOptional: boolean
  // The one real-world event (if any) that auto-completes this step on
  // a project the moment it happens -- '' means none. See
  // execution_step_service.try_auto_fill.
  triggerKey: string | null
}

export interface ProjectExecutionStep {
  id: string
  name: string
  sequenceNumber: number
  weightPercentage: number
  stageKey: string
  isOptional: boolean
  isExcluded: boolean
  excludedReason: string | null
  completionPercentage: number
  remarks: string | null
  // Set when this step was checked complete through the "were any
  // additional services rendered?" flow rather than as part of the
  // project's original quoted scope -- see ScopeExecutionPanel.vue.
  isAdditionalScope?: boolean
  contractCovered?: boolean | null
  triggerKey?: string | null
  // Added directly on this project rather than snapshotted from its
  // assigned step set -- can be deleted outright, unlike a
  // template-derived step, which can only ever be excluded.
  isCustom?: boolean
}

export interface ExecutionStepBulkItem {
  id: string
  completionPercentage: number
  remarks: string | null
  isExcluded: boolean
  excludedReason: string | null
}
