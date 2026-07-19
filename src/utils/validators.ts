import type { ValidationRule } from '@/types/Validation'

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
}
