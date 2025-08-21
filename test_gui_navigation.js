const { chromium } = require('playwright');

async function testGUINavigation() {
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // Enable console logging
  page.on('console', msg => {
    if (msg.type() === 'log') {
      console.log('Browser console:', msg.text());
    }
  });
  
  try {
    console.log('1. Loading app...');
    await page.goto('http://localhost:1420', { waitUntil: 'networkidle' });
    
    // Check current URL
    console.log('   Current URL:', page.url());
    
    // Check if we're on license page
    const licenseButton = await page.$('button:has-text("Start Trial")');
    if (licenseButton) {
      console.log('2. Found license page, clicking Start Trial...');
      await licenseButton.click();
      await page.waitForTimeout(2000);
      console.log('   New URL:', page.url());
    }
    
    // Check for navigation
    console.log('\n3. Looking for navigation elements...');
    const navLinks = await page.$$('nav a, aside a, [role="navigation"] a');
    console.log(`   Found ${navLinks.length} navigation links`);
    
    // Get all link texts
    const linkTexts = await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll('a'));
      return links.map(link => ({
        text: link.textContent?.trim(),
        href: link.getAttribute('href')
      }));
    });
    console.log('   Navigation links:', JSON.stringify(linkTexts, null, 2));
    
    // Try to navigate to folders directly
    console.log('\n4. Navigating directly to /folders...');
    await page.goto('http://localhost:1420/folders', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // Check what's on the page now
    const pageTitle = await page.title();
    const pageText = await page.textContent('body');
    console.log('   Page title:', pageTitle);
    console.log('   Page contains "Folders":', pageText.includes('Folders'));
    console.log('   Page contains "License":', pageText.includes('License'));
    
    // Check if FolderManagement component is rendered
    const folderElements = await page.evaluate(() => {
      const elements = [];
      // Check for specific elements from FolderManagement component
      const selectors = [
        '.folder-item',
        '[class*="folder"]',
        'button[title="Add Folder"]',
        'h2:has-text("Folders")',
        'button:has-text("Index")',
        'button:has-text("Segment")',
        'button:has-text("Upload")',
        'button:has-text("Share")'
      ];
      
      selectors.forEach(selector => {
        try {
          const el = document.querySelector(selector);
          if (el) {
            elements.push({
              selector,
              found: true,
              text: el.textContent?.substring(0, 50)
            });
          }
        } catch (e) {}
      });
      
      return elements;
    });
    console.log('\n5. FolderManagement elements found:', JSON.stringify(folderElements, null, 2));
    
    // Check React Router
    console.log('\n6. Checking React Router...');
    const routerInfo = await page.evaluate(() => {
      // Check if React Router is present
      const root = document.getElementById('root');
      const hasRouter = root?.innerHTML.includes('react-router') || 
                        root?.innerHTML.includes('Route') ||
                        window.location.pathname !== '/';
      return {
        hasRouter,
        pathname: window.location.pathname,
        rootHTML: root?.innerHTML.substring(0, 500)
      };
    });
    console.log('   Router info:', JSON.stringify(routerInfo, null, 2));
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await browser.close();
  }
}

testGUINavigation().catch(console.error);