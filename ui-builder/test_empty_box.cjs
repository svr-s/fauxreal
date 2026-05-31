const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: "new" });
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
  
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle2' });
  
  // Wait for the form to load
  await page.waitForSelector('form');
  
  // Find the button that says "Add FixedVariables" or similar
  // It's inside the FixedVariables section.
  const buttons = await page.$$('button');
  for (let btn of buttons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Add FixedVariables') || text.includes('Add fixed_variables')) {
      console.log('Found Add button, clicking...');
      await btn.click();
      break;
    }
  }
  
  // Wait a moment for React to render
  await new Promise(r => setTimeout(r, 1000));
  
  // Get the HTML of the first item in the FixedVariables array
  const formHtml = await page.evaluate(() => {
    // try to find the array item container
    const items = document.querySelectorAll('.group\\/item');
    if (items.length > 0) {
      return items[0].innerHTML;
    }
    return 'No item found';
  });
  
  console.log('HTML of added item:', formHtml);
  
  await browser.close();
})();
