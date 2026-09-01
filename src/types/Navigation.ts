import type { RouteNameValue } from '@/types/Route'

export interface NavItem {
  label: string
  routeName: RouteNameValue
  icon: string
  matchPath: string
  /** Hidden from the nav for every role except Administrator -- kept in
   * sync with the adminOnly route meta these routes carry (see
   * router/index.ts), so a non-admin never even sees the entry point. */
  adminOnly?: boolean
}
