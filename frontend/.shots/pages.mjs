import { chromium } from 'playwright'
import { readFileSync } from 'fs'

const EXE = `${process.env.LOCALAPPDATA}/ms-playwright/chromium-1228/chrome-win64/chrome.exe`
const token = readFileSync('.shots/token.txt', 'utf8').trim()

const ROUTES = [
  ['/', 'dashboard'],
  ['/accounts', 'accounts'],
  ['/logs', 'logs'],
  ['/statistics', 'statistics'],
  ['/platforms', 'platforms'],
  ['/settings', 'settings'],
]

const browser = await chromium.launch({ executablePath: EXE })
const ctx = await browser.newContext({ viewport: { width: 1440, height: 950 }, deviceScaleFactor: 2 })

// 先落地一次以便写 localStorage
const boot = await ctx.newPage()
await boot.goto('http://localhost:3000/login')
await boot.evaluate(t => {
  localStorage.setItem('anyrouter_token', t)
  localStorage.setItem('token', t)
  localStorage.setItem('anyrouter-theme', 'dark')
}, token)
await boot.close()

const errors = []
const page = await ctx.newPage()
page.on('console', m => { if (m.type() === 'error') errors.push(`[${m.location().url.split('/').pop()}] ${m.text()}`) })
page.on('pageerror', e => errors.push(`PAGEERROR ${e.message}`))

for (const [route, name] of ROUTES) {
  await page.goto(`http://localhost:3000${route}`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(1600)
  await page.screenshot({ path: `.shots/p-${name}.png`, fullPage: false })
  console.log(`${name}: ${await page.title()} | url=${page.url().replace('http://localhost:3000','')}`)
}

console.log('\nERRORS:', errors.length ? '\n  ' + [...new Set(errors)].slice(0, 12).join('\n  ') : 'none')
await browser.close()
