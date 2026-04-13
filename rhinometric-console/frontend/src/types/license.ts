// ------------------------------------------------------------------
// Rhinometric License Contract v3.0 ? SERVICE-BASED MODEL
// ------------------------------------------------------------------

/**
 * License plans: starter | growth | scale
 */
export type LicensePlan = 'starter' | 'growth' | 'scale';

/**
 * License status from the backend.
 */
export type LicenseStatus =
  | 'valid'
  | 'active'
  | 'about_to_expire'
  | 'expired'
  | 'invalid'
  | 'missing'
  | 'error';

/**
 * User/role usage sub-object from the API.
 */
export interface LicenseUsers {
  owner: number;
  owner_limit: number;
  admins_used: number;
  admins_limit: number;
  operators_used: number;
  operators_limit: number;
  viewers_used: number;
  viewers_limit: number;
}

/**
 * Full license status response from GET /api/license/status
 */
export interface LicenseStatusResponse {
  // Plan
  plan: string;
  plan_display: string;

  // Services
  max_services: number;
  services_used: number;
  remaining_services: number;
  extra_services_used: number;
  price_per_extra_service: number;

  // Users
  users: LicenseUsers;

  // Metadata
  tenant_id: string | null;
  organization: string | null;
  expires_at: string | null;
  issued_at: string | null;
  edition: string;
  features: string[];

  // Status
  status: string;
  is_valid: boolean;
  message: string;
  warning: string | null;
  days_remaining: number | null;
  hours_remaining: number | null;
  validator: string;
  breaches: string[] | null;
}

// Keep legacy types for compat ? not used by new code
export type LicenseEdition = 'trial' | 'annual_standard' | 'enterprise' | 'demo_cloud';
export type LicenseModule = 'core' | 'ai_anomalies' | 'dashboards' | 'veriverde';
export interface LicensePayload {
  license_id: string;
  customer_name: string;
  customer_contact?: string;
  edition: LicenseEdition;
  max_hosts: number;
  modules: LicenseModule[];
  issued_at: string;
  valid_from: string;
  valid_until: string;
  notes?: string;
  install_id?: string;
  issuer?: string;
}
