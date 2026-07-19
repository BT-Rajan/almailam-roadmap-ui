import type { RouteNameValue } from '@/types/Route'

export interface NavItem {
  label: string
  routeName: RouteNameValue
  icon: string
  matchPath: string
}
