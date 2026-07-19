import { computed, reactive } from 'vue'
import type { ValidationRules, FieldError } from '@/types/Validation'

export function useFormValidation(initialRules?: ValidationRules) {
  const errors = reactive<Record<string, string>>({})
  const rules = reactive<ValidationRules>(initialRules || {})

  const setRules = (newRules: ValidationRules) => {
    Object.assign(rules, newRules)
  }

  const validateField = (fieldName: string, value: any): boolean => {
    const fieldRules = rules[fieldName]
    if (!fieldRules) {
      delete errors[fieldName]
      return true
    }

    for (const rule of fieldRules) {
      const result = rule(value)
      if (result !== true) {
        errors[fieldName] = result
        return false
      }
    }

    delete errors[fieldName]
    return true
  }

  const validateAll = (data: Record<string, any>): boolean => {
    let isValid = true
    for (const fieldName in rules) {
      if (!validateField(fieldName, data[fieldName])) {
        isValid = false
      }
    }
    return isValid
  }

  const clearErrors = (fieldName?: string) => {
    if (fieldName) {
      delete errors[fieldName]
    } else {
      Object.keys(errors).forEach((key) => {
        delete errors[key]
      })
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
