import type { ValidationRule } from '@/types/Validation'
import { addDaysIso, todayIso } from '@/utils/dateFormatter'

export const validators = {
  required: (message = 'This field is required'): ValidationRule => (value) => {
    if (value === null || value === undefined || value === '' || (Array.isArray(value) && value.length === 0)) {
      return message
    }
    return true
  },

  email: (message = 'Please enter a valid email address'): ValidationRule => (value) => {
    if (!value) return true
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(String(value)) ? true : message
  },

  minLength: (min: number, message?: string): ValidationRule => (value) => {
    if (!value) return true
    const msg = message || `Minimum length is ${min} characters`
    return String(value).length >= min ? true : msg
  },

  maxLength: (max: number, message?: string): ValidationRule => (value) => {
    if (!value) return true
    const msg = message || `Maximum length is ${max} characters`
    return String(value).length <= max ? true : msg
  },

  pattern: (regex: RegExp, message = 'Invalid format'): ValidationRule => (value) => {
    if (!value) return true
    return regex.test(String(value)) ? true : message
  },

  number: (message = 'Please enter a valid number'): ValidationRule => (value) => {
    if (!value && value !== 0) return true
    return !Number.isNaN(Number(value)) ? true : message
  },

  positive: (message = 'Please enter a positive number'): ValidationRule => (value) => {
    if (!value && value !== 0) return true
    return Number(value) > 0 ? true : message
  },

  min: (minValue: number, message?: string): ValidationRule => (value) => {
    if (!value && value !== 0) return true
    const msg = message || `Minimum value is ${minValue}`
    return Number(value) >= minValue ? true : msg
  },

  max: (maxValue: number, message?: string): ValidationRule => (value) => {
    if (!value && value !== 0) return true
    const msg = message || `Maximum value is ${maxValue}`
    return Number(value) <= maxValue ? true : msg
  },

  match: (fieldValue: unknown, message = 'Fields do not match'): ValidationRule => (value) => {
    return value === fieldValue ? true : message
  },

  url: (message = 'Please enter a valid URL'): ValidationRule => (value) => {
    if (!value) return true
    try {
      new URL(String(value))
      return true
    } catch {
      return message
    }
  },

  phone: (message = 'Please enter a valid phone number'): ValidationRule => (value) => {
    if (!value) return true
    const phoneRegex = /^[\d\s\-\+\(\)]+$/
    return phoneRegex.test(String(value)) && String(value).replace(/\D/g, '').length >= 10 ? true : message
  },

  // Both ISO "YYYY-MM-DD" date-only strings, compared lexicographically
  // (correct for that format) rather than parsed as Date objects, to
  // avoid a timezone-shift edge case at day boundaries.
  notPastDate: (message = 'This date cannot be in the past'): ValidationRule => (value) => {
    if (!value) return true
    return String(value) >= todayIso() ? true : message
  },

  notFutureDate: (message = 'This date cannot be in the future'): ValidationRule => (value) => {
    if (!value) return true
    return String(value) <= todayIso() ? true : message
  },

  // ISO "YYYY-MM-DD" date-only, same lexicographic-comparison convention
  // as notPastDate/notFutureDate above.
  maxDaysFromToday: (days: number, message?: string): ValidationRule => (value) => {
    if (!value) return true
    const msg = message || `This date cannot be more than ${days} days from today`
    return String(value) <= addDaysIso(todayIso(), days) ? true : msg
  },

  // `getOtherValue` is read at validation time (not when setRules() is
  // called), so it can safely be a closure over a reactive field --
  // e.g. `validators.notBeforeDate(() => form.startDate)` -- to keep the
  // comparison live as the other field changes. `strict: true` requires
  // the date to be strictly after (same day fails too), for pairs where
  // the backend itself enforces that (see ProjectCreate.target_after_start).
  notBeforeDate: (getOtherValue: () => unknown, message = 'This date cannot be before the start date', strict = false): ValidationRule => (value) => {
    const other = getOtherValue()
    if (!value || !other) return true
    return (strict ? String(value) > String(other) : String(value) >= String(other)) ? true : message
  },
}
