// -----------------------------------------------------------------
// Rhinometric License Contract v2.6 - TypeScript Interfaces
// -----------------------------------------------------------------
//
// Define la forma canonica del contrato de licencia y la
// respuesta normalizada que consume el frontend.
//
// NOTA: Algunos campos aun no estan disponibles en la API actual
// y se mapean desde campos legacy. Ver TODO markers.
// -----------------------------------------------------------------

/**
 * Edicion (plan) de la licencia.
 * TODO: Cuando el backend migre al nuevo schema, asegurar que
 * el campo "edition" use estos valores exactos.
 */
export type LicenseEdition = 'trial' | 'annual_standard' | 'enterprise' | 'demo_cloud';

/**
 * Modulos habilitados en la licencia.
 * TODO: Confirmar lista final con el equipo de producto.
 */
export type LicenseModule = 'core' | 'ai_anomalies' | 'dashboards' | 'veriverde';

/**
 * Contrato de licencia tal como lo firma el servidor de licencias.
 *
 * Campos marcados con TODO aun no estan disponibles en la API actual
 * y se mapean desde los campos legacy del backend.
 */
export interface LicensePayload {
  /** Identificador unico de la licencia (actualmente: tenant_id o license_key) */
  license_id: string;

  /** Nombre del cliente / organizacion */
  customer_name: string;

  /** Email de contacto del cliente */
  customer_contact?: string;

  /** Edicion / plan de la licencia */
  edition: LicenseEdition;

  /** Numero maximo de hosts permitidos */
  max_hosts: number;

  /**
   * Modulos habilitados.
   * TODO: El backend actualmente envia "features" como string[].
   * Mapear features -> modules cuando la API se actualice.
   */
  modules: LicenseModule[];

  /** Fecha de emision de la licencia (ISO 8601) */
  issued_at: string;

  /**
   * Inicio de validez de la licencia (ISO 8601).
   * TODO: No disponible en la API actual. Se usa issued_at como fallback.
   */
  valid_from: string;

  /** Fin de validez de la licencia (ISO 8601) */
  valid_until: string;

  /** Notas adicionales */
  notes?: string;

  /**
   * Identificador unico de la instalacion.
   * TODO: Actualmente mapeado desde tenant_id.
   */
  install_id?: string;

  /** Entidad emisora de la licencia */
  issuer?: string;

  // signature: string; -- Solo en el backend / Rust validator (no expuesta al frontend)
}

/**
 * Estado normalizado de la licencia para el frontend.
 *
 * valid           - Licencia valida y activa
 * about_to_expire - Valida pero expira en <=30 dias
 * expired         - Licencia expirada
 * invalid         - Firma incorrecta o formato no reconocido
 * missing         - No se encontro archivo de licencia
 * error           - No se pudo contactar el servicio de licencias
 */
export type LicenseStatus =
  | 'valid'
  | 'about_to_expire'
  | 'expired'
  | 'invalid'
  | 'missing'
  | 'error';

/**
 * Respuesta del endpoint /api/license/status adaptada al frontend.
 */
export interface LicenseStatusResponse {
  /** Estado normalizado de la licencia */
  status: LicenseStatus;

  /** Motivo legible del estado (especialmente para invalid/error) */
  reason?: string;

  /** Payload completo de la licencia (solo si status !== 'missing' y !== 'error') */
  license?: LicensePayload;

  // -- Campos operativos (del backend actual) --

  /** Hosts actualmente monitorizados */
  hosts_used: number;

  /** Hosts disponibles */
  hosts_available: number;

  /** Dias restantes hasta expiracion */
  days_remaining?: number;

  /** Horas restantes (para demo_cloud) */
  hours_remaining?: number;

  /** Mensaje de advertencia (host limit, expiracion proxima) */
  warning?: string;

  /** Validador utilizado: "rust" | "legacy" */
  validator?: string;
}
