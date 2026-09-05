export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'

export type ComponentSize = 'sm' | 'md' | 'lg'

export type BadgeVariant = 'neutral' | 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'ai'

export interface SelectOption {
  label: string
  value: string
  disabled?: boolean
  /** i18n key resolved by SelectBox/RadioGroup instead of `label` when present.
   * `label` stays the English fallback for options with no static translation
   * (e.g. runtime data from a catalog). */
  labelKey?: string
}
