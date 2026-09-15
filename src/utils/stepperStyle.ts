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
    // 'upcoming' used text-text-muted (neutral-400, #a3a3ad in light
    // mode) here -- against the card's near-white background that's
    // roughly 2.3:1 contrast, well under WCAG's 4.5:1 floor for normal
    // text, and reads as barely-there pale grey ("silver") rather than
    // a legibly de-emphasized label. text-text-secondary (neutral-500)
    // is the same shade already used for every other secondary-but-
    // readable label in the app (see main.css's --color-text-secondary).
    status === 'current' ? 'font-semibold text-info-600' : 'text-text-secondary',
  ]
}
