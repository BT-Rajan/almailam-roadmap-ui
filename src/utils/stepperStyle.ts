export type StepStatus = 'complete' | 'current' | 'upcoming'

// Shared "bar" stepper segment coloring -- complete = green, current =
// info (blue), upcoming = neutral border. Used by both Stepper.vue's
// bar variant (client/project creation wizards) and WorkflowProgress.vue
// (project workspace + the parallel Design/Permit/Supervision band), so
// the three-color convention only has one implementation to keep in
// sync. Width/shrink is caller-specific -- a wizard/linear step wants
// w-full to fill its column, a parallel-band tick wants a fixed w-6 --
// so callers append their own sizing class on top of this base.
export function stepBarClasses(status: StepStatus): string[] {
  return [
    'h-1.5 rounded-full transition-colors duration-fast cursor-pointer hover:brightness-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500',
    status === 'complete' ? 'bg-success-500' : '',
    status === 'current' ? 'bg-info-500' : '',
    status === 'upcoming' ? 'bg-border-default' : '',
  ]
}

export function stepLabelClasses(status: StepStatus): string[] {
  return [
    'truncate text-xs hover:text-accent-600 cursor-pointer',
    status === 'current' ? 'font-semibold text-info-600' : 'text-text-muted',
  ]
}
