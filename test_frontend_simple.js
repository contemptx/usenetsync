// Simple test to check current state
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  
  // Capture console messages
  const logs = [];
  page.on('console', msg => {
    logs.push(`[${msg.type()}] ${msg.text()}`);
  });
  
  try {
    await page.goto('http://localhost:1420', { waitUntil: 'networkidle0' });
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Get page content
    const bodyText = await page.evaluate(() => document.body.innerText);
    
    console.log('=== CURRENT PAGE STATE ===');
    console.log('Page shows:', bodyText.split('\n')[0]); // First line
    
    // Check if it's the license screen
    if (bodyText.includes('Activate UsenetSync')) {
      console.log('✅ License activation screen is displayed');
      
      // Try clicking "Start Trial"
      await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const trialButton = buttons.find(b => b.textContent.includes('Start Trial'));
        if (trialButton) {
          trialButton.click();
          return true;
        }
        return false;
      });
      
      // Wait for navigation
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Check new content
      const newContent = await page.evaluate(() => document.body.innerText);
      console.log('\nAfter clicking Start Trial:');
      console.log('Page shows:', newContent.split('\n')[0]);
      
      if (newContent.includes('Dashboard')) {
        console.log('✅ Dashboard is now visible!');
      }
    }
    
    // Check for errors
    const hasErrors = logs.some(log => log.includes('[error]'));
    if (hasErrors) {
      console.log('\n❌ Console errors:');
      logs.filter(log => log.includes('[error]')).forEach(log => console.log(log));
    } else {
      console.log('\n✅ No console errors');
    }
    
    await page.screenshot({ path: 'frontend_current.png' });
    console.log('\nScreenshot saved to frontend_current.png');
    
  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    await browser.close();
  }
})();