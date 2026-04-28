export interface LicenseStatusResponse {
  status: string
  message?: string
  edition?: string
  plan_display: string
  customer_name?: string
  customer_email?: string
  valid_from?: string
  valid_until?: string
  max_hosts?: number
  max_users?: number
  max_integrations?: number
  usage?: {
    hosts?: number
    users?: number
    integrations?: number
    [k: string]: any
  }
  modules?: Array<{
    name?: string
    enabled?: boolean
    usage?: number
    limit?: number
    status?: string
    [k: string]: any
  }>
  features?: string[]
  [k: string]: any
}
