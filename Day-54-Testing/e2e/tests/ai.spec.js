// e2e/tests/ai.spec.js
import { test, expect } from '@playwright/test'

async function registerAndLogin(page) {
  const email = `e2e_ai_${Date.now()}@test.com`
  await page.goto('/login')
  await page.getByRole('button', { name: /register/i }).click()
  await page.fill('input[placeholder*="name"]', 'AI User')
  await page.fill('input[type="email"]', email)
  await page.fill('input[type="password"]', 'testpassword123')
  await page.getByRole('button', { name: /create account/i }).click()
  await expect(page).toHaveURL(/\/board/, { timeout: 10000 })
}

test.describe('AI Features', () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page)
  })

  test('AI Expand button is present in form', async ({ page }) => {
    await expect(page.locator('button', { hasText: /AI Expand/i }).first()).toBeVisible()
  })

  test('AI Prioritize button is present in form', async ({ page }) => {
    await expect(page.locator('button', { hasText: /AI Prioritize/i }).first()).toBeVisible()
  })

  test('AI Expand fills description', async ({ page }) => {
    const titleInput = page.locator('input[placeholder*="title"]').first()
    await titleInput.fill('Add dark mode to dashboard')

    const expandBtn = page.locator('button', { hasText: /AI Expand/i }).first()
    await expandBtn.click()

    // Wait for description to be filled (AI response)
    await expect(
      page.locator('textarea').first()
    ).not.toHaveValue('', { timeout: 15000 })
  })

  test('AI weekly summary loads', async ({ page }) => {
    // Click Generate Weekly Summary button in AI Panel
    const summaryBtn = page.locator('button', { hasText: /weekly summary/i })
    await expect(summaryBtn).toBeVisible()
    await summaryBtn.click()

    // Stats or summary should appear
    await expect(
      page.locator('text=/completed|tasks|week/i').first()
    ).toBeVisible({ timeout: 15000 })
  })
})