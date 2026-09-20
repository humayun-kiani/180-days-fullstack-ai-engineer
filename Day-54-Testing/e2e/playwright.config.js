import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,   // run sequentially (share auth state)
  retries: 1,
  timeout: 30_000,

  reporter: [['html', { open: 'never' }], ['list']],

  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'off',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
  ],

  // Global setup: ensure app is running
  webServer: {
    command: 'echo "Start app manually before running E2E tests"',
    url: 'http://localhost:5173',
    reuseExistingServer: true,
    timeout: 5000
  }
})