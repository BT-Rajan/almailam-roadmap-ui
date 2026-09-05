import type { RouteNameValue } from '@/types/Route'

export interface NavItem {
  /** i18n key under the `navigation` namespace, resolved by SidebarItem.vue -- not display text. */
  labelKey: string
  routeName: RouteNameValue
  icon: string
  matchPath: string
  /** Hidden from the nav for every role except Administrator -- kept in
   * sync with the adminOnly route meta these routes carry (see
   * router/index.ts), so a non-admin never even sees the entry point. */
  adminOnly?: boolean
}
