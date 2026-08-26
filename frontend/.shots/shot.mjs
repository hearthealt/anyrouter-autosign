import { chromium } from 'playwright'

// 本地 playwright 期望 chromium-1234，环境里只有 1228。
// 截图用途下这点版本差无影响，直接指定已有可执行文件，省掉一次极慢的下载。
const EXE = `${process.env.LOCALAPPDATA}/ms-playwright/chromium-1228/chrome-win64/chrome.exe`

const url = process.argv[2] ?? 'http://localhost:3000/ui-lab'
const name = process.argv[3] ?? 'lab'
const themes = (process.argv[4] ?? 'light,dark').split(',')

const browser = await chromium.launch({ executablePath: EXE })
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 2 })

const errors = []
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()) })
page.on('pageerror', e => errors.push(`PAGEERROR: ${e.message}`))

await page.goto(url, { waitUntil: 'networkidle' })
await page.waitForTimeout(1200)

for (const theme of themes) {
  await page.evaluate(t => document.documentElement.setAttribute('data-theme', t), theme)
  await page.waitForTimeout(500)
  await page.screenshot({ path: `.shots/${name}-${theme}.png`, fullPage: true })
}

console.log('ERRORS:', errors.length ? '\n  ' + errors.slice(0, 10).join('\n  ') : 'none')
await browser.close()
