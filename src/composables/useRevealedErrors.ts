import { computed, ref, watch, type ComputedRef } from 'vue'

// Companion to useFormValidation's `reveal` option, for forms that build
// their own error maps (computed from the form, or filled by a validate()
// function) instead of going through useFormValidation.
//
// The errors are still computed live -- they gate Next/Save exactly as
// before -- but what the form *displays* follows the app-wide rule: a
// field shows its error once the user's edits have changed it, or once a
// save / next-step attempt calls reveal(). A blank form doesn't open
// covered in red.

type ErrorMap = Record<string, string | undefined>

interface RevealedErrors<E extends ErrorMap> {
  /** The errors to display. */
  errors: ComputedRef<E>
  /** Show every current error (a save / next-step attempt). */
  reveal: () => void
  /** Start over, e.g. when a dialog is reopened for a different record. */
  reset: () => void
}

/**
 * For a flat map of field -> message. A field counts as changed by the
 * user once its message differs from the first one seen for it: a blank
 * required field typed into ("required" -> valid, or -> "invalid email").
 * A field's first appearance only sets its starting point, so fields that
 * show up because of another choice (Individual -> Company adds the
 * organisation fields) aren't red before they're touched.
 */
export function useRevealedErrors<E extends ErrorMap>(source: () => E): RevealedErrors<E> {
  const revealedAll = ref(false)
  const changed = ref(new Set<string>())
  let baseline: ErrorMap | null = null

  watch(
    source,
    (current) => {
      if (baseline === null) {
        baseline = { ...current }
        return
      }
      for (const key of Object.keys(current)) {
        if (!(key in baseline)) baseline[key] = current[key]
      }
      for (const key of Object.keys(baseline)) {
        if ((baseline[key] || undefined) !== (current[key] || undefined) && !changed.value.has(key)) {
          changed.value = new Set(changed.value).add(key)
        }
      }
    },
    { immediate: true, deep: true },
  )

  const errors = computed(() => {
    const current = source()
    if (revealedAll.value) return current
    const shown: ErrorMap = {}
    for (const key of Object.keys(current)) {
      if (changed.value.has(key)) shown[key] = current[key]
    }
    return shown as E
  })

  return {
    errors,
    reveal: () => {
      revealedAll.value = true
    },
    reset: () => {
      revealedAll.value = false
      changed.value = new Set()
      baseline = { ...source() }
    },
  }
}

/**
 * For a list of rows (installments, contacts) with one error map per row.
 * A row shows its errors once any of its own values changed, so a freshly
 * added blank row isn't red before anything is typed into it.
 */
export function useRevealedRowErrors<R extends object, E extends ErrorMap>(
  rows: () => R[],
  rowErrors: () => E[],
): { errors: ComputedRef<E[]>; reveal: () => void } {
  const revealedAll = ref(false)
  const firstSeen = new WeakMap<R, string>()
  // Plain (non-reactive) set; `version` tells `errors` when it grew.
  const changedRows = new WeakSet<R>()
  const version = ref(0)

  watch(
    rows,
    (current) => {
      let anyNew = false
      for (const row of current) {
        const snapshot = JSON.stringify(row)
        const initial = firstSeen.get(row)
        if (initial === undefined) {
          firstSeen.set(row, snapshot)
        } else if (initial !== snapshot && !changedRows.has(row)) {
          changedRows.add(row)
          anyNew = true
        }
      }
      if (anyNew) version.value++
    },
    { immediate: true, deep: true },
  )

  const errors = computed(() => {
    void version.value
    const currentRows = rows()
    return rowErrors().map((rowError, index) =>
      revealedAll.value || changedRows.has(currentRows[index]) ? rowError : ({} as E),
    )
  })

  return {
    errors,
    reveal: () => {
      revealedAll.value = true
    },
  }
}
