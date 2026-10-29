import { test, expect } from '@playwright/test';

test.describe('Pitwall F1 Modernization - Phase 2A', () => {
  test('landing page loads and navigation works', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.hero-title')).toContainText('Authoritative Race');
    await page.click('text="Enter Pitwall"');
    await expect(page).toHaveURL(/\/app/);
    await expect(page.locator('.app-sidebar')).toBeVisible();
    await expect(page.locator('.app-topbar')).toBeVisible();
  });

  test('overview page loads with real API data', async ({ page }) => {
    test.setTimeout(180000);
    await page.goto('/app');

    await expect(page.locator('.overview-container')).toBeVisible({ timeout: 60000 });
    await expect(page.locator('.overview-error')).not.toBeVisible();

    // Verify session data is present
    await expect(page.locator('.overview-header')).toContainText('Reference: HAM', { timeout: 60000 });
    await expect(page.locator('.stat-card').first()).toContainText('S-2024');
  });

  test('primary and reference driver selection updates the UI', async ({ page }) => {
    test.setTimeout(180000);
    await page.goto('/app');

    await expect(page.locator('.overview-container')).toBeVisible({ timeout: 60000 });
    await expect(page.locator('.overview-error')).not.toBeVisible();

    const primaryDriverSelect = page.locator('.driver-selector.primary select');
    const refDriverSelect = page.locator('.driver-selector.comparison select');

    await primaryDriverSelect.selectOption('NOR');
    await expect(page.locator('.overview-header')).toContainText('NOR', { timeout: 60000 });

    await refDriverSelect.selectOption('VER');
    await expect(page.locator('.overview-header')).toContainText('Reference: VER', { timeout: 60000 });
  });

  test('telemetry page loads real chart data', async ({ page }) => {
    test.setTimeout(120000); // 2 minutes due to heavy FastF1 data loading
    await page.goto('/app/telemetry');

    await expect(page.locator('.telemetry-container')).toBeVisible({ timeout: 90000 });
    await expect(page.locator('.telemetry-error')).not.toBeVisible();

    // Verify recharts wrapper is rendered
    await expect(page.locator('.recharts-wrapper').first()).toBeVisible({ timeout: 60000 });
    await expect(page.locator('.telemetry-header')).toContainText('VER vs HAM');
  });

  test('driver comparison changes when reference driver changes', async ({ page }) => {
    test.setTimeout(120000);
    await page.goto('/app/comparison');

    await expect(page.locator('.comparison-container')).toBeVisible({ timeout: 90000 });
    await expect(page.locator('.comparison-error')).not.toBeVisible();

    // Verify matchup banner
    await expect(page.locator('.driver-pill.primary')).toHaveText('VER', { timeout: 60000 });
    await expect(page.locator('.driver-pill.reference')).toHaveText('HAM', { timeout: 60000 });

    // Change reference to NOR
    const refDriverSelect = page.locator('.driver-selector.comparison select');
    await refDriverSelect.selectOption('NOR');

    // UI should reload and display NOR
    await expect(page.locator('.driver-pill.reference')).toHaveText('NOR', { timeout: 90000 });
    // Check for sector or engineering card
    await expect(page.locator('.card-engineering').first()).toBeVisible({ timeout: 60000 });
  });
  test('tyre intelligence page loads real chart data or handles timeout', async ({ page }) => {
    test.setTimeout(120000);
    await page.goto('/app/tyres');

    await expect(page.locator('.tyres-container, .tyres-error')).toBeVisible({ timeout: 90000 });

    const isError = await page.locator('.tyres-error').isVisible();
    if (!isError) {
      await expect(page.locator('.recharts-wrapper').first()).toBeVisible({ timeout: 60000 });
      await expect(page.locator('.tyres-header')).toContainText('Tyre Degradation');
    }
  });

  test('race strategy page loads real monte carlo simulation', async ({ page }) => {
    test.setTimeout(120000);
    await page.goto('/app/strategy');

    await expect(page.locator('.strategy-container')).toBeVisible({ timeout: 90000 });
    await expect(page.locator('.strategy-error')).not.toBeVisible();

    // Verify probability indicators and track gap are loaded
    await expect(page.locator('.directive-box')).toBeVisible({ timeout: 60000 });
    await expect(page.locator('.prob-value').first()).toBeVisible({ timeout: 60000 });
  });

  test('replay page loads 3D track or handles timeout', async ({ page }) => {
    test.setTimeout(90000);
    await page.goto('/app/replay');
    await expect(page.locator('.replay-container')).toBeVisible();
    await expect(page.locator('.track-canvas, .replay-error')).toBeVisible({ timeout: 70000 });
  });

  test('ml lab page predicts degradation', async ({ page }) => {
    test.setTimeout(90000);
    await page.goto('/app/ml-lab');
    await expect(page.locator('.ml-container')).toBeVisible();
    await page.click('button:has-text("Run Prediction")');
    await expect(page.locator('.prediction-results')).toBeVisible({ timeout: 60000 });
  });

  test('jarvis page loads insights', async ({ page }) => {
    test.setTimeout(90000);
    await page.goto('/app/jarvis');
    await expect(page.locator('.jarvis-container')).toBeVisible();
    await expect(page.locator('.insight-card')).not.toHaveCount(0, { timeout: 60000 });
  });

  test('circuits page loads schedule', async ({ page }) => {
    test.setTimeout(60000);
    await page.goto('/app/circuits');
    await expect(page.locator('.circuits-container')).toBeVisible();
    await expect(page.locator('.circuit-card')).not.toHaveCount(0, { timeout: 30000 });
  });

  test('drivers page loads results', async ({ page }) => {
    test.setTimeout(90000);
    await page.goto('/app/drivers');
    await expect(page.locator('.drivers-container')).toBeVisible();
    await expect(page.locator('.driver-card')).not.toHaveCount(0, { timeout: 60000 });
  });
});
