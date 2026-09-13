// বাংলা মন্তব্য: Universal Zero-Complexity Interface — shared contract barrel।
export * from './connection-contract';
export * from './capability-contract';
export * from './execution-mode';
export { capabilityFromModule, explainUnavailable, ADD_INTENTS } from './capability';
export type { UserCapability, UserCapabilityStatus, UnavailableCapability, AddIntent } from './capability';
