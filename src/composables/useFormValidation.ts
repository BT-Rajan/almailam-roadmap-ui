import { computed, reactive } from 'vue'
import type { ValidationRules, FieldError } from '@/types/Validation'

interface ValidateOptions {
  /**
   * Show the resulting errors immediately (a save / next-step attempt).
   * Live re-validation while someone is filling the form passes false:
   * the errors are still computed, but a field only shows its error once
   * it has been changed or a save has been attempted -- a blank form
   * doesn't open covered in red.
   */
  reveal?: boolean
}

export function useFormValidation(initialRules?: ValidationRules) {
  // Every current error, whether or not it is shown yet.
  const allErrors: Record<string, string> = {}
  // What the form displays: errors of fields that were changed, or that a
  // save attempt revealed.
  const errors = reactive<Record<string, string>>({})
  const rules = reactive<ValidationRules>(initialRules || {})
  // A field's value the first time it was validated, to detect a change.
  const initialValues: Record<string, string> = {}
  const shownFields = new Set<string>()

  const serialize = (value: unknown): string => {
    try {
      return JSON.stringify(value) ?? ''
    } catch {
      return String(value)
    }
  }

  const syncShown = (fieldName: string) => {
    if (shownFields.has(fieldName) && allErrors[fieldName]) {
      errors[fieldName] = allErrors[fieldName]
    } else {
      delete errors[fieldName]
    }
  }

  const trackChange = (fieldName: string, value: unknown) => {
    const current = serialize(value)
    if (!(fieldName in initialValues)) {
      initialValues[fieldName] = current
    } else if (initialValues[fieldName] !== current) {
      shownFields.add(fieldName)
    }
  }

  const setRules = (newRules: ValidationRules) => {
    Object.assign(rules, newRules)
  }

  const validateField = (fieldName: string, value: unknown, options: ValidateOptions = {}): boolean => {
    const { reveal = true } = options
    trackChange(fieldName, value)
    if (reveal) shownFields.add(fieldName)

    let error: string | undefined
    for (const rule of rules[fieldName] ?? []) {
      const result = rule(value)
      if (result !== true) {
        error = result
        break
      }
    }

    if (error) {
      allErrors[fieldName] = error
    } else {
      delete allErrors[fieldName]
    }
    syncShown(fieldName)
    return !error
  }

  const validateAll = (data: Record<string, unknown>, options: ValidateOptions = {}): boolean => {
    let isValid = true
    for (const fieldName in data) {
      if (!validateField(fieldName, data[fieldName], options)) {
        isValid = false
      }
    }
    return isValid
  }

  const clearErrors = (fieldName?: string) => {
    const fields = fieldName ? [fieldName] : Object.keys(allErrors)
    for (const field of fields) {
      delete allErrors[field]
      delete errors[field]
    }
  }

  const getFieldError = (fieldName: string) => computed(() => errors[fieldName])

  const getErrors = computed(() => {
    const fieldErrors: FieldError[] = []
    for (const fieldName in errors) {
      fieldErrors.push({
        field: fieldName,
        message: errors[fieldName],
      })
    }
    return fieldErrors
  })

  const hasErrors = computed(() => Object.keys(errors).length > 0)

  return {
    errors,
    rules,
    setRules,
    validateField,
    validateAll,
    clearErrors,
    getFieldError,
    getErrors,
    hasErrors,
  }
}
