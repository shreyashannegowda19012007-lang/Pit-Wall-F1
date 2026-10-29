import { test, expect } from '@playwright/test';

test.describe('Live Race Command Center', () => {
  test.setTimeout(90000); // FastF1 data fetching can take up to 60s without cache

  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:5173/app/command-center');
  });

  test('Command Center loads and displays session info', async ({ page }) => {
    // Check header
    await expect(page.locator('.cc-header-info h1')).toBeVisible({ timeout: 60000 });
    const headerText = await page.locator('.cc-header-info h1').textContent();
    expect(headerText).toContain('SPAIN');
    
    // Check primary driver
    await expect(page.locator('.cc-driver-name').first()).toBeVisible();
    await expect(page.locator('.cc-driver-name').first()).toHaveText('VER');
    
    // Check reference driver in Rival Watch panel
    await expect(page.locator('.cc-rival-watch .cc-driver-name')).toBeVisible();
    await expect(page.locator('.cc-rival-watch .cc-driver-name')).toHaveText('HAM');
  });

  test('Timing and Tyre information renders', async ({ page }) => {
    // Verify metric grid loads
    await expect(page.locator('.cc-metric-label', { hasText: 'Last Lap' }).first()).toBeVisible({ timeout: 60000 });
    await expect(page.locator('.cc-metric-label', { hasText: 'Tyre' }).first()).toBeVisible();
  });

  test('Strategy information renders', async ({ page }) => {
    // Verify Strategy Status panel
    await expect(page.locator('.cc-panel-header', { hasText: 'STRATEGY STATUS' })).toBeVisible({ timeout: 60000 });
    await expect(page.locator('.cc-metric-label', { hasText: 'Recommendation' })).toBeVisible();
  });

  test('JARVIS summary renders', async ({ page }) => {
    // Verify Jarvis Engineering panel
    await expect(page.locator('.cc-panel-header', { hasText: 'JARVIS ENGINEERING' })).toBeVisible({ timeout: 60000 });
  });

  test('Driver switching works', async ({ page }) => {
    await page.waitForSelector('.cc-header-info h1', { timeout: 60000 });
    // Switch primary driver
    const primarySelect = page.locator('.driver-selector.primary select');
    await primarySelect.selectOption('NOR');
    
    await expect(page.locator('.cc-driver-name').first()).toHaveText('NOR', { timeout: 30000 });
    
    // Switch reference driver
    const refSelect = page.locator('.driver-selector.comparison select');
    await refSelect.selectOption('LEC');
    
    await expect(page.locator('.cc-rival-watch .cc-driver-name')).toHaveText('LEC', { timeout: 30000 });
  });
});
