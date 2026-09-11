// For more info, see https://github.com/storybookjs/eslint-plugin-storybook#configuration-flat-config-format
import storybook from "eslint-plugin-storybook";

import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'


export default tseslint.config({ ignores: ['dist', 'dist-admin', 'dist-user', 'src/dataconnect-generated', 'coverage', 'node_modules'] }, {
  extends: [
    js.configs.recommended,
    ...tseslint.configs.recommended,
  ],
  files: ['**/*.{ts,tsx}'],
  languageOptions: {
    ecmaVersion: 2020,
    globals: globals.browser,
  },
  plugins: {
    'react-hooks': reactHooks,
    'react-refresh': reactRefresh,
  },
  rules: {
    ...reactHooks.configs.recommended.rules,
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true, allowExportNames: ['useTheme', 'useToast', 'useI18n', 'useThemeSync', 'useSwarmStream', 'setSujonState', 'useSujonState', 'SUJON_STATE_EVENT', 'SujonState', 'Theme', 'THEME_ORDER', 'ToastType', 'Toast', 'globalShowToastRef', 'useSujonMetrics', 'SujonHealthIndicator', 'SujonDashboardGrid', 'useSwarmArchitect', 'useAuthStatus', 'useSystemHealth', 'workspaceFeatureRoutes', 'SwarmArchitect'] },
    ],
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/no-unused-vars': ['warn', { 'argsIgnorePattern': '^_', 'varsIgnorePattern': '^_' }],
    'react-hooks/set-state-in-effect': 'off',
    'no-console': ['warn', { allow: ['warn', 'error', 'debug'] }],
  },
}, {
  // Test files: Allow any in tests (mocks, stubs, test fixtures)
  files: ['**/*.{test,spec}.{ts,tsx}', '**/test/**/*.{ts,tsx}'],
  rules: {
    '@typescript-eslint/no-explicit-any': 'off',
  },
}, {
  // Routes and config files export route objects, not React components
  files: ['**/routes/**/*.{ts,tsx}', '**/routes.{ts,tsx}'],
  rules: {
    'react-refresh/only-export-components': 'off',
  },
}, storybook.configs["flat/recommended"], {
  // বাংলা মন্তব্য: eslint-plugin-storybook v10 framework প্যাকেজ থেকে ইম্পোর্ট চায়, কিন্তু
  // ইনস্টল করা Storybook 8-এ @storybook/react-vite থেকে Meta/StoryObj এক্সপোর্ট হয় না।
  files: ['**/*.stories.{ts,tsx}'],
  rules: {
    'storybook/no-renderer-packages': 'off',
  },
});
