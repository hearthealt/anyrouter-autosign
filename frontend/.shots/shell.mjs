import { chromium } from 'playwright'
const EXE = `${process.env.LOCALAPPDATA}/ms-playwright/chromium-1228/chrome-win64/chrome.exe`
const browser = await chromium.launch({ executablePath: EXE })
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 })
const errors = []
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()) })
page.on('pageerror', e => errors.push(`PAGEERROR: ${e.message}`))
await page.goto('http://localhost:3000/ui-lab', { waitUntil: 'networkidle' })
await page.waitForTimeout(1400)
for (const theme of ['dark', 'light']) {
  await page.evaluate(t => document.documentElement.setAttribute('data-theme', t), theme)
  await page.waitForTimeout(500)
  // 只截首屏，看外壳
  await page.screenshot({ path: `.shots/shell-${theme}.png` })
}
console.log('ERRORS:', errors.length ? '\n  ' + errors.slice(0, 8).join('\n  ') : 'none')
await browser.close()
