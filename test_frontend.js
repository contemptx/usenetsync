// Simple test to check if Dashboard renders without errors
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  
  // Capture console errors
  const errors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });
  
  page.on('pageerror', error => {
    errors.push(error.toString());
  });

  try {
    // Navigate to the app
    await page.goto('http://localhost:1420', { waitUntil: 'networkidle0' });
    
    // Wait a bit for any async errors
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Check page title
    const title = await page.title();
    console.log('Page title:', title);
    
    // Check if Dashboard is rendered
    const dashboardExists = await page.evaluate(() => {
      return document.querySelector('[class*="Dashboard"]') !== null ||
             document.body.textContent.includes('Dashboard') ||
             document.body.textContent.includes('Total Files');
    });
    
    console.log('Dashboard rendered:', dashboardExists);
    
    if (errors.length > 0) {
      console.log('\n❌ Console errors found:');
      errors.forEach(err => console.log('  -', err));
    } else {
      console.log('\n✅ No console errors!');
    }
    
    // Take a screenshot
    await page.screenshot({ path: 'frontend_test.png' });
    console.log('Screenshot saved to frontend_test.png');
    
  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    await browser.close();
  }
})();