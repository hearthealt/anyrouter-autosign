import { chromium } from 'playwright'
const EXE = `${process.env.LOCALAPPDATA}/ms-playwright/chromium-1228/chrome-win64/chrome.exe`
const browser = await chromium.launch({ executablePath: EXE })
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 4 })
await page.goto('http://localhost:3000/ui-lab', { waitUntil: 'networkidle' })
await page.waitForTimeout(1000)

for (const theme of ['light', 'dark']) {
  await page.evaluate(t => document.documentElement.setAttribute('data-theme', t), theme)
  await page.waitForTimeout(400)
  // 包含 checkbox + switch 的那一行：用 :has() 精确定位
  await page.locator('.lab__row:has(.ui-switch)').screenshot({ path: `.shots/sw-${theme}.png` })
  await page.locator('.lab__row:has(.ui-badge-wrap)').screenshot({ path: `.shots/bg-${theme}.png` })
}
await browser.close()
console.log('ok')
