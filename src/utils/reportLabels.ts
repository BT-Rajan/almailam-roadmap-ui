import { useI18n } from 'vue-i18n'

/** "In Progress" -> "inProgress", "Payment Plan" -> "paymentPlan". */
function camelKey(value: string): string {
  return value
    .trim()
    .split(/[^A-Za-z0-9]+/)
    .filter(Boolean)
    .map((word, index) => (index === 0 ? word.charAt(0).toLowerCase() : word.charAt(0).toUpperCase()) + word.slice(1))
    .join('')
}

/**
 * Translates an enum value the backend sends (a task/document/project
 * status, a stage) via `<namespace>.<camelCased value>`, falling back to
 * the value itself when no translation exists -- a new status still shows,
 * just untranslated.
 */
export function useEnumLabel() {
  const { t, te } = useI18n()
  return (namespace: string, value: string): string => {
    const key = `${namespace}.${camelKey(value)}`
    return te(key) ? t(key) : value
  }
}
