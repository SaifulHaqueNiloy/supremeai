// Backward compatibility shim for components/sujon
// Canonical module: frontend/src/components/widgets/TelemetryDashboardWidget.tsx

export {
  useRealtimeTelemetryMetrics as useSujonMetrics,
  TelemetryHealthIndicator as SujonHealthIndicator,
  TelemetryDashboardGrid as SujonDashboardGrid,
  type MetricData,
  type TelemetryWidgetProps as SujonWidgetProps,
} from '../widgets/TelemetryDashboardWidget';
