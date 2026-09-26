/**
 * E2E Guest Chat smoke — the public demo surface, hermetically.
 *
 * The guest chat on / is a LOCAL demo (responseFor() in PublicPages.tsx is a
 * canned marketing teaser — it never calls the backend). That makes it a
 * pure frontend contract, ideal for a hermetic E2E lane: the only network
 * activity is incidental (health/auth polling), which the catch-all API
 * blocker below keeps from reaching any baked-in production URL.
 *
 * CONTRACTS UNDER TEST (from src/pages/PublicPages.tsx):
 *   - Send button is empty-gated (disabled={!input.trim() || typing}).
 *   - Intent chips fill the composer with their canned prompt.
 *   - Enter submits; Shift+Enter inserts a newline (composing-safe handler).
 *   - Submit → user bubble immediately, typing indicator (role=status), then
 *     the canned assistant reply after the 650ms demo timer; the typing
 *     indicator resolves and the reply is keyed to the prompt content.
 *   - Double-submit guard: a second submit while typing is a no-op (one user
 *     bubble, not two).
 *   - "Start a new chat" resets the conversation back to the landing state.
 *   - After the first exchange the sign-in nudge appears.
 *   - ModelPicker selection updates the composer footer label.
 */
import { test, expect, type Page, type Route } from '@playwright/test';

async function blockApi(page: Page) {
  // Hermetic runner: no request may reach the baked-in production backend
  // from CI. Registered before navigation so it wins for every request.
  await page.route('**/api/**', (route: Route) => route.fulfill({ status: 204, body: '' }));
}

test.describe('Guest chat demo smoke', () => {
  test.beforeEach(async ({ page }) => {
    await blockApi(page);
    await page.goto('/');
  });

  test('send button is empty-gated until the composer has content', async ({ page }) => {
    const send = page.getByRole('button', { name: 'Send message' });
    await expect(send).toBeDisabled();
    await page.getByLabel('Message SupremeAI').fill('hello there');
    await expect(send).toBeEnabled();
  });

  test('intent chip fills the composer with its canned prompt', async ({ page }) => {
    await page.getByRole('button', { name: 'Research' }).click();
    await expect(page.getByLabel('Message SupremeAI')).toHaveValue(/research/i);
    await expect(page.getByRole('button', { name: 'Send message' })).toBeEnabled();
  });

  test('typed continuation after an intent chip is separated by a space (no mush)', async ({ page }) => {
    const composer = page.getByLabel('Message SupremeAI');
    await page.getByRole('button', { name: 'Research' }).click();
    await composer.pressSequentially('What is SupremeAI?');
    // The canned prompt ends with '.', typed text must start after a space
    // (the chip appends "prompt + ' '").
    await expect(composer).toHaveValue(/findings\. What is SupremeAI\?$/);
    await composer.press('Enter');
    const bubble = page.locator('.animate-guest-bubble-in').first();
    await expect(bubble).toContainText('findings. What is SupremeAI?');
  });

  test('user bubble renders the canned prompt dimmed ahead of the typed words', async ({ page }) => {
    const composer = page.getByLabel('Message SupremeAI');
    await page.getByRole('button', { name: 'Analyze' }).click();
    await composer.pressSequentially('my problem');
    await composer.press('Enter');
    const prefixSpan = page.locator('.animate-guest-bubble-in span').first();
    await expect(prefixSpan).toHaveClass(/text-slate-400/);
    await expect(prefixSpan).toHaveText(/Help me analyze this problem/);
  });

  test('Enter submits but Shift+Enter only inserts a newline', async ({ page }) => {
    const composer = page.getByLabel('Message SupremeAI');
    await composer.pressSequentially('first line');
    await composer.press('Shift+Enter');
    await composer.pressSequentially('second line');
    // No submit: the landing hero is still up (it yields to the thread only
    // once a message exists).
    await expect(page.getByRole('heading', { name: /What would you like to work on/i })).toBeVisible();

    await composer.press('Enter');
    await expect(page.getByText(/first line/)).toBeVisible();
  });

  test('submit shows the user bubble, typing state, then the assistant reply', async ({ page }) => {
    await page.getByLabel('Message SupremeAI').fill('Help me build a plan');
    await page.getByRole('button', { name: 'Send message' }).click();

    // User bubble appears immediately.
    await expect(page.getByText('Help me build a plan')).toBeVisible();
    // Demo typing state is announced to AT (role=status) ...
    await expect(page.getByRole('status', { name: 'Assistant is typing' })).toBeVisible();
    // ... and resolves into the canned "plan" reply (650ms demo timer).
    await expect(page.getByText(/practical plan/i)).toBeVisible({ timeout: 5_000 });
    await expect(page.getByRole('status', { name: 'Assistant is typing' })).toHaveCount(0);
  });

  test('double-submit while typing adds only one user bubble', async ({ page }) => {
    const composer = page.getByLabel('Message SupremeAI');
    await composer.fill('count my bubbles');
    await composer.press('Enter');
    // Second Enter lands inside the 650ms typing window; the submit guard
    // (if (!value || typing) return) must swallow it.
    await composer.press('Enter');

    await expect(page.getByText(/count my bubbles/)).toHaveCount(1, { timeout: 5_000 });
  });

  test('Start a new chat resets back to the landing state', async ({ page }) => {
    await page.getByLabel('Message SupremeAI').fill('hello');
    await page.getByRole('button', { name: 'Send message' }).click();
    await expect(page.getByText(/think that through/i)).toBeVisible({ timeout: 5_000 });

    await page.getByRole('button', { name: 'Start a new chat' }).click();
    await expect(page.getByRole('heading', { name: /What would you like to work on/i })).toBeVisible();
    await expect(page.getByText(/think that through/i)).toHaveCount(0);
  });

  test('sign-in nudge appears after the first exchange', async ({ page }) => {
    await expect(page.getByText(/Your conversation is temporary/i)).toHaveCount(0);
    await page.getByLabel('Message SupremeAI').fill('hello');
    await page.getByRole('button', { name: 'Send message' }).click();
    await expect(page.getByText(/Your conversation is temporary/i)).toBeVisible();
  });

  test('model picker selection updates the footer label', async ({ page }) => {
    await page.getByRole('button', { name: /Supreme Auto/ }).click();
    await page.getByRole('button', { name: /Reasoning Pro/ }).click();
    await expect(page.getByText(/Reasoning Pro · temporary session/)).toBeVisible();
  });
});

test.describe('Public marketing pages render', () => {
  const routes: { path: string; heading: RegExp }[] = [
    { path: '/models', heading: /Choose the outcome/i },
    { path: '/features', heading: /.+/ },
    { path: '/pricing', heading: /.+/ },
    { path: '/docs', heading: /.+/ },
    { path: '/about', heading: /.+/ },
  ];

  for (const { path, heading } of routes) {
    test(`${path} renders its page heading`, async ({ page }) => {
      await blockApi(page);
      await page.goto(path);
      await expect(page.getByRole('heading', { level: 1 }).first()).toBeVisible();
      if (heading.source !== '.+') {
        await expect(page.getByRole('heading', { level: 1, name: heading })).toBeVisible();
      }
      // Every public page funnels back into the chat. The CTA label is
      // page-specific ("Try in chat", "Try it in guest chat", "Start with the
      // product", "Meet your first agent", …) — assert the funnel TARGET
      // (an in-main link back to "/") instead of copy that each page owns.
      // FIX (CI red 36219425476): the old label regex only matched /models,
      // breaking the four pages #1514 gave distinct copy to.
      await expect(page.locator('main a[href="/"]').first()).toBeVisible();
    });
  }
});
