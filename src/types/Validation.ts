export type ValidationRule = (value: unknown) => string | true

export interface ValidationRules {
  [fieldName: string]: ValidationRule[]
}

export interface FieldError {
  field: string
  message: string
}

export type ValidationResult = FieldError[]
