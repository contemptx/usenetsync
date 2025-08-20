// Detailed test to check what's actually rendered
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  
  try {
    await page.goto('http://localhost:1420', { waitUntil: 'networkidle0' });
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Get page content
    const bodyText = await page.evaluate(() => document.body.innerText);
    console.log('Page content preview:');
    console.log(bodyText.substring(0, 500));
    
    // Check for specific elements
    const elements = await page.evaluate(() => {
      return {
        hasApp: !!document.querySelector('#root'),
        hasRouter: !!document.querySelector('[class*="Router"]'),
        hasDashboard: !!document.querySelector('[class*="Dashboard"]'),
        hasNavigation: !!document.querySelector('nav'),
        hasLogin: document.body.innerText.includes('Login') || document.body.innerText.includes('Sign'),
        hasLicense: document.body.innerText.includes('License') || document.body.innerText.includes('Activate'),
        hasError: document.body.innerText.includes('Error') || document.body.innerText.includes('error'),
        classNames: Array.from(document.querySelectorAll('*')).map(el => el.className).filter(c => c && c.includes('container')).slice(0, 5)
      };
    });
    
    console.log('\nElement checks:', elements);
    
    // Check current URL
    const url = page.url();
    console.log('\nCurrent URL:', url);
    
  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    await browser.close();
  }
})();