// e2e/tests/tasks.spec.js
import { test, expect } from '@playwright/test'

// Helper: register and log in
async function registerAndLogin(page) {
  const email = `e2e_tasks_${Date.now()}@test.com`
  await page.goto('/login')
  await page.getByRole('button', { name: /register/i }).click()
  await page.fill('input[placeholder*="name"]', 'Task User')
  await page.fill('input[type="email"]', email)
  await page.fill('input[type="password"]', 'testpassword123')
  await page.getByRole('button', { name: /create account/i }).click()
  await expect(page).toHaveURL(/\/board/, { timeout: 10000 })
}

test.describe('Task Management', () => {
  test.beforeEach(async ({ page }) => {
    await registerAndLogin(page)
  })

  test('creates a new task', async ({ page }) => {
    const title = `E2E Test Task ${Date.now()}`

    await page.fill('input[placeholder*="title"]', title)
    await page.getByRole('button', { name: /create task/i }).click()

    // Task should appear in the board
    await expect(page.locator(`text=${title}`)).toBeVisible({ timeout: 10000 })
  })

  test('creates task with high priority', async ({ page }) => {
    const title = `High Priority Task ${Date.now()}`

    await page.fill('input[placeholder*="title"]', title)
    await page.locator('button', { hasText: 'high' }).first().click()
    await page.getByRole('button', { name: /create task/i }).click()

    await expect(page.locator(`text=${title}`)).toBeVisible({ timeout: 10000 })
  })

  test('board shows three columns', async ({ page }) => {
    // Check for To Do, In Progress, Done columns (desktop)
    await page.setViewportSize({ width: 1280, height: 720 })

    await expect(page.locator('text=To Do')).toBeVisible()
    await expect(page.locator('text=In Progress')).toBeVisible()
    await expect(page.locator('text=Done')).toBeVisible()
  })

  test('search opens with keyboard shortcut', async ({ page }) => {
    await page.keyboard.press('Control+k')
    await expect(page.locator('input[placeholder*="Search"]')).toBeVisible({ timeout: 5000 })
  })

  test('search modal closes with Escape', async ({ page }) => {
    await page.keyboard.press('Control+k')
    await expect(page.locator('input[placeholder*="Search"]')).toBeVisible()
    await page.keyboard.press('Escape')
    await expect(page.locator('input[placeholder*="Search"]')).not.toBeVisible()
  })

  test('keyboard shortcut ? opens help', async ({ page }) => {
    await page.keyboard.press('?')
    await expect(page.locator('text=Keyboard Shortcuts')).toBeVisible({ timeout: 5000 })
  })
})