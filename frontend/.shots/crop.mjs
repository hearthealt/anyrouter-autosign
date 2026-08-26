import { chromium } from 'playwright'
const EXE = `${process.env.LOCALAPPDATA}/ms-playwright/chromium-1228/chrome-win64/chrome.exe`
const browser = await chromium.launch({ executablePath: EXE })
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 3 })
await page.goto('http://localhost:3000/ui-lab', { waitUntil: 'networkidle' })
await page.waitForTimeout(1000)

for (const theme of ['light', 'dark']) {
  await page.evaluate(t => document.documentElement.setAttribute('data-theme', t), theme)
  await page.waitForTimeout(400)
  // 勾选/开关那一行
  const rows = await page.locator('.lab__row').all()
  await rows[3].screenshot({ path: `.shots/switches-${theme}.png` })   // checkbox + switch 行
  await rows[5].screenshot({ path: `.shots/badges-${theme}.png` })     // badge 行
}
await browser.close()
console.log('ok')
