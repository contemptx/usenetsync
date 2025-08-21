const { chromium } = require('playwright');

async function inspectFoldersPage() {
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // Enable console logging
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('Browser console error:', msg.text());
    }
  });
  
  try {
    console.log('Loading app...');
    await page.goto('http://localhost:1420', { waitUntil: 'networkidle' });
    
    // Start trial if needed
    const licenseButton = await page.$('button:has-text("Start Trial")');
    if (licenseButton) {
      await licenseButton.click();
      await page.waitForTimeout(1000);
    }
    
    // Navigate to Folders
    console.log('\nNavigating to Folders page...');
    await page.goto('http://localhost:1420/folders', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // Get the entire page HTML
    const html = await page.content();
    console.log('\n=== PAGE HTML (first 2000 chars) ===');
    console.log(html.substring(0, 2000));
    
    // Get all text content
    const text = await page.textContent('body');
    console.log('\n=== PAGE TEXT CONTENT ===');
    console.log(text);
    
    // Check for React components
    const reactComponents = await page.evaluate(() => {
      const components = [];
      document.querySelectorAll('[data-reactroot], [data-react-component], #root > *').forEach(el => {
        components.push({
          tag: el.tagName,
          class: el.className,
          text: el.textContent?.substring(0, 100)
        });
      });
      return components;
    });
    console.log('\n=== REACT COMPONENTS ===');
    console.log(JSON.stringify(reactComponents, null, 2));
    
    // Check for any elements with "folder" in class or id
    const folderElements = await page.evaluate(() => {
      const elements = [];
      document.querySelectorAll('[class*="folder" i], [id*="folder" i]').forEach(el => {
        elements.push({
          tag: el.tagName,
          class: el.className,
          id: el.id,
          text: el.textContent?.substring(0, 50)
        });
      });
      return elements;
    });
    console.log('\n=== FOLDER-RELATED ELEMENTS ===');
    console.log(JSON.stringify(folderElements, null, 2));
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await browser.close();
  }
}

inspectFoldersPage().catch(console.error);