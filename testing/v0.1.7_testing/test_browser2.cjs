const puppeteer = require('puppeteer');
const handler = require('serve-handler');
const http = require('http');

const server = http.createServer((request, response) => {
  return handler(request, response, { public: '../docs' });
});

server.listen(3000, async () => {
  console.log('Running at http://localhost:3000');
  const browser = await puppeteer.launch({ headless: "new" });
  const page = await browser.newPage();
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
  await page.goto('http://localhost:3000/fauxreal/', { waitUntil: 'networkidle2' });
  await browser.close();
  server.close();
});
