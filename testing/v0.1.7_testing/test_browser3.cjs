const puppeteer = require('puppeteer');
(async () => {
  console.log('Testing live site...');
  const browser = await puppeteer.launch({ headless: "new" });
  const page = await browser.newPage();
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
  await page.goto('https://svr-s.github.io/fauxreal/', { waitUntil: 'networkidle2' });
  await browser.close();
})();
