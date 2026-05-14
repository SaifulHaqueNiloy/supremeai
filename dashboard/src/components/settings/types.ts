export interface SystemConfig {
  id?: string;
  activeModel?: string;
  smallModel?: string;
  version?: number;
  maintenanceMode?: boolean;
  fullAuthority?: boolean;
  shareMode?: string;
  enableExternalDirectory?: boolean;
  emailNotifications?: boolean;
  smsAlerts?: boolean;
  systemMessage?: string;
  tierQuotas?: Record<string, number>;
  tierMaxApis?: Record<string, number>;
  tierMaxSimulatorInstalls?: Record<string, number>;
  timeouts?: Record<string, number>;
  thresholds?: Record<string, number>;
  settings?: Record<string, any>;
  collections?: Record<string, string>;
}
