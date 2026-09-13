// ════════════════════════════════════════════════════════════════════
// ✅ HELPER FUNCTIONS
// (Extracted verbatim from AdminBrowserPanel.tsx — mechanical refactor)
// ════════════════════════════════════════════════════════════════════

/**
 * Attempts to extract text content from iframe for AI context
 * Handles cross-origin restrictions gracefully
 */
export async function getPageContent(): Promise<string> {
  return ''; // Implement based on your proxy setup
}

export function formatLinksFromData(links: Record<string, unknown>[]): string {
  if (!links?.length) return 'No links found.';
  return `🔗 **Links Extracted (${links.length} found)**\n\n${
    links.map((link: Record<string, unknown>, i: number) => `${i+1}. [${link.text || link.url}](${link.url})`).join('\n')
  }`;
}

export function formatIssuesFromData(issues: Record<string, unknown>[]): string {
  if (!issues?.length) return '✅ No issues found!';

  const critical = issues.filter((i: Record<string, unknown>) => i.severity === 'critical');
  const warnings = issues.filter((i: Record<string, unknown>) => i.severity === 'warning');

  return `🚨 **Issues Detected (${issues.length} total)**\n\n**Critical (${critical.length}):**\n${
    critical.map((i: Record<string, unknown>) => `- ⚠️ ${i.message}`).join('\n') || 'None'
  }\n\n**Warnings (${warnings.length}):**\n${
    warnings.map((i: Record<string, unknown>) => `- ⚡ ${i.message}`).join('\n') || 'None'
  }\n\n**Suggestions:** Run security scan for detailed remediation steps.`;
}
