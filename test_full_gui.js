const { chromium } = require('playwright');

async function testFullGUI() {
  console.log('='.repeat(60));
  console.log('TESTING COMPLETE GUI WORKFLOW');
  console.log('='.repeat(60));

  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  // Monitor API calls
  page.on('request', request => {
    if (request.url().includes('/api/')) {
      console.log(`→ API: ${request.method()} ${request.url().replace('http://localhost:8000', '')}`);
    }
  });

  try {
    console.log('\n1. Loading application...');
    await page.goto('http://localhost:1420', { waitUntil: 'networkidle' });
    
    // Start trial to get past license page
    console.log('\n2. Starting trial...');
    const trialButton = await page.$('button:has-text("Start Trial")');
    if (trialButton) {
      await trialButton.click();
      await page.waitForTimeout(2000);
      console.log('   ✓ Clicked Start Trial');
    }
    
    // Now we should be in the main app
    console.log('\n3. Checking navigation...');
    await page.waitForTimeout(1000);
    
    // Get all navigation items
    const navItems = await page.evaluate(() => {
      const items = document.querySelectorAll('.sidebar a, nav a, [class*="nav"] a, aside a');
      return Array.from(items).map(a => a.textContent.trim());
    });
    console.log('   Navigation items:', navItems);
    
    // Look for Folders link
    console.log('\n4. Navigating to Folders...');
    const foldersLink = await page.$('a:has-text("Folders")') || 
                       await page.$('a:has-text("Folder Management")') ||
                       await page.$('text=Folders');
    
    if (foldersLink) {
      await foldersLink.click();
      await page.waitForTimeout(2000);
      console.log('   ✓ Navigated to Folders page');
      
      // Take screenshot
      await page.screenshot({ path: '/tmp/folders_page.png', fullPage: true });
      console.log('   ✓ Screenshot saved to /tmp/folders_page.png');
      
      // Check for tabs
      console.log('\n5. Checking for tabs...');
      const tabs = await page.evaluate(() => {
        const tabButtons = document.querySelectorAll('button');
        return Array.from(tabButtons)
          .map(b => b.textContent.trim())
          .filter(text => ['Overview', 'Files', 'Segments', 'Shares', 'Actions'].some(t => text.includes(t)));
      });
      console.log('   Tabs found:', tabs);
      
      // Check for Add Folder button
      console.log('\n6. Looking for Add Folder button...');
      const addButton = await page.$('button:has-text("Add Folder")') ||
                       await page.$('button:has-text("Add")');
      
      if (addButton) {
        console.log('   ✓ Found Add Folder button');
        const buttonText = await addButton.textContent();
        console.log('   Button text:', buttonText);
        
        // Click it
        console.log('\n7. Testing Add Folder...');
        await addButton.click();
        await page.waitForTimeout(2000);
        
        // Check what happened
        const hasDialog = await page.$('[role="dialog"], .modal, [class*="dialog"]');
        const hasFileInput = await page.$('input[type="file"]');
        
        if (hasDialog) {
          console.log('   ✓ Dialog opened');
        } else if (hasFileInput) {
          console.log('   ✓ File input triggered');
        } else {
          console.log('   ⚠ No visible response to Add Folder click');
        }
      } else {
        console.log('   ✗ Add Folder button not found');
      }
      
      // Check folder list area
      console.log('\n8. Checking folder list...');
      const folderList = await page.evaluate(() => {
        // Look for folder list container
        const containers = document.querySelectorAll('[class*="folder"], [class*="Folder"]');
        const folderTexts = [];
        containers.forEach(c => {
          const text = c.textContent.trim();
          if (text && !text.includes('Add Folder')) {
            folderTexts.push(text.substring(0, 100));
          }
        });
        return folderTexts;
      });
      
      if (folderList.length > 0) {
        console.log('   Folders in list:', folderList.length);
        folderList.slice(0, 3).forEach(f => console.log('   -', f));
      } else {
        console.log('   No folders in list (expected for new installation)');
      }
      
      // Test each tab if they exist
      for (const tabName of ['Overview', 'Files', 'Segments', 'Shares', 'Actions']) {
        const tab = await page.$(`button:has-text("${tabName}")`);
        if (tab) {
          console.log(`\n9. Testing ${tabName} tab...`);
          await tab.click();
          await page.waitForTimeout(500);
          
          // Get tab content
          const content = await page.evaluate(() => {
            const main = document.querySelector('main, .main-content, [class*="flex-1"]');
            return main ? main.textContent.trim().substring(0, 200) : 'No content';
          });
          console.log(`   ${tabName} content preview:`, content);
        }
      }
      
    } else {
      console.log('   ✗ Could not find Folders link in navigation');
      
      // Get current page content for debugging
      const pageContent = await page.evaluate(() => document.body.innerText);
      console.log('\n   Current page content:');
      console.log(pageContent.substring(0, 500));
    }
    
  } catch (error) {
    console.error('\n✗ Error:', error.message);
    await page.screenshot({ path: '/tmp/error.png' });
    console.log('Error screenshot saved to /tmp/error.png');
  } finally {
    await browser.close();
  }
  
  console.log('\n' + '='.repeat(60));
  console.log('TEST COMPLETE');
  console.log('='.repeat(60));
}

testFullGUI().catch(console.error);