// Comprehensive GUI test to check all functionality
const puppeteer = require('puppeteer');

async function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function testGUI() {
  const browser = await puppeteer.launch({ 
    headless: false, // Set to false to see what's happening
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  
  // Capture console errors
  const errors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
    console.log(`[${msg.type()}] ${msg.text()}`);
  });
  
  page.on('pageerror', error => {
    errors.push(error.toString());
    console.log('[PAGE ERROR]', error);
  });

  try {
    console.log('\n=== 1. LOADING APP ===');
    await page.goto('http://localhost:1420', { waitUntil: 'networkidle0' });
    await delay(2000);
    
    // Check if license screen appears
    const bodyText = await page.evaluate(() => document.body.innerText);
    if (bodyText.includes('Activate UsenetSync')) {
      console.log('✓ License screen loaded');
      
      // Click Start Trial
      await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const trialButton = buttons.find(b => b.textContent.includes('Start Trial'));
        if (trialButton) trialButton.click();
      });
      await delay(2000);
    }
    
    console.log('\n=== 2. TESTING NAVIGATION ===');
    // Get all navigation links
    const navLinks = await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll('nav a, [role="navigation"] a, a[href*="/"]'));
      return links.map(a => ({
        text: a.textContent.trim(),
        href: a.href
      }));
    });
    console.log('Found navigation links:', navLinks);
    
    console.log('\n=== 3. TESTING FOLDER MANAGEMENT ===');
    // Try to navigate to Folder Management
    const folderMgmtClicked = await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll('a'));
      const folderLink = links.find(a => 
        a.textContent.includes('Folder') || 
        a.textContent.includes('Manage') ||
        a.href.includes('folder')
      );
      if (folderLink) {
        folderLink.click();
        return true;
      }
      return false;
    });
    
    if (folderMgmtClicked) {
      await delay(2000);
      console.log('✓ Navigated to Folder Management');
      
      // Check for folder management elements
      const folderElements = await page.evaluate(() => {
        return {
          hasSelectButton: !!document.querySelector('button:contains("Select"), button:contains("Browse")'),
          hasIndexButton: !!document.querySelector('button:contains("Index")'),
          hasFolderList: !!document.querySelector('[class*="folder"], [class*="Folder"]'),
          pageContent: document.body.innerText.substring(0, 200)
        };
      });
      console.log('Folder Management elements:', folderElements);
      
      // Try to click Select Folder button
      const selectClicked = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        const selectBtn = buttons.find(b => 
          b.textContent.includes('Select') || 
          b.textContent.includes('Browse') ||
          b.textContent.includes('Add')
        );
        if (selectBtn) {
          console.log('Clicking button:', selectBtn.textContent);
          selectBtn.click();
          return true;
        }
        return false;
      });
      
      if (selectClicked) {
        await delay(1000);
        console.log('✓ Clicked folder select button');
      }
    }
    
    console.log('\n=== 4. TESTING UPLOAD ===');
    // Navigate to Upload
    const uploadClicked = await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll('a'));
      const uploadLink = links.find(a => 
        a.textContent.includes('Upload') || 
        a.href.includes('upload')
      );
      if (uploadLink) {
        uploadLink.click();
        return true;
      }
      return false;
    });
    
    if (uploadClicked) {
      await delay(2000);
      console.log('✓ Navigated to Upload');
      
      // Check upload page elements
      const uploadElements = await page.evaluate(() => {
        return {
          hasFileSelect: !!document.querySelector('button:contains("Select Files"), input[type="file"]'),
          hasUploadButton: !!document.querySelector('button:contains("Upload"), button:contains("Start")'),
          hasShareOptions: document.body.innerText.includes('Share') || document.body.innerText.includes('Public'),
          pageContent: document.body.innerText.substring(0, 200)
        };
      });
      console.log('Upload page elements:', uploadElements);
    }
    
    console.log('\n=== 5. TESTING SHARES ===');
    // Navigate to Shares
    const sharesClicked = await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll('a'));
      const shareLink = links.find(a => 
        a.textContent.includes('Share') || 
        a.href.includes('share')
      );
      if (shareLink) {
        shareLink.click();
        return true;
      }
      return false;
    });
    
    if (sharesClicked) {
      await delay(2000);
      console.log('✓ Navigated to Shares');
      
      // Check shares page
      const shareElements = await page.evaluate(() => {
        return {
          hasShareList: !!document.querySelector('[class*="share"], [class*="Share"]'),
          hasCreateButton: !!document.querySelector('button:contains("Create"), button:contains("New")'),
          pageContent: document.body.innerText.substring(0, 200)
        };
      });
      console.log('Shares page elements:', shareElements);
    }
    
    console.log('\n=== 6. CHECKING FOR ERRORS ===');
    if (errors.length > 0) {
      console.log('❌ Found errors:');
      errors.forEach(err => console.log('  -', err));
    } else {
      console.log('✓ No console errors');
    }
    
    // Take screenshots
    await page.screenshot({ path: 'gui_test_final.png', fullPage: true });
    console.log('\n✓ Screenshot saved to gui_test_final.png');
    
  } catch (error) {
    console.error('Test failed:', error);
  } finally {
    await delay(2000);
    await browser.close();
  }
}

testGUI();