// e2e/tests/auth.spec.js
import { test, expect } from '@playwright/test'

const uniqueEmail = () => `e2e_${Date.now()}@test.com`

test.describe('Authentication', () => {
  test('redirects to login when unauthenticated', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveURL(/\/login/)
  })

  test('shows login form', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible()
  })

  test('shows register form on tab switch', async ({ page }) => {
    await page.goto('/login')
    await page.getByRole('button', { name: /register/i }).click()
    await expect(page.getByPlaceholder(/your name/i)).toBeVisible()
  })

  test('registers new user successfully', async ({ page }) => {
    const email = uniqueEmail()
    await page.goto('/login')
    await page.getByRole('button', { name: /register/i }).click()

    await page.fill('input[placeholder*="name"]', 'E2E User')
    await page.fill('input[type="email"]', email)
    await page.fill('input[type="password"]', 'testpassword123')
    await page.getByRole('button', { name: /create account/i }).click()

    await expect(page).toHaveURL(/\/board/, { timeout: 10000 })
    await expect(page.locator('text=TaskMind')).toBeVisible()
  })

  test('shows error for wrong password', async ({ page }) => {
    await page.goto('/login')

    await page.fill('input[type="email"]', 'nonexistent@test.com')
    await page.fill('input[type="password"]', 'wrongpassword')
    await page.getByRole('button', { name: /sign in/i }).click()

    // Toast or error message should appear
    await expect(
      page.locator('text=/invalid|incorrect|failed/i')
    ).toBeVisible({ timeout: 5000 })
  })
})