const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  console.log('='.repeat(60));
  console.log('TESTING FOLDER DISPLAY AFTER FIX');
  console.log('='.repeat(60));
  
  // Monitor API calls
  page.on('request', request => {
    if (request.url().includes('/api/v1/folders')) {
      console.log(`→ Folders API called`);
    }
  });
  
  page.on('response', response => {
    if (response.url().includes('/api/v1/folders')) {
      console.log(`← Folders API response: ${response.status()}`);
    }
  });
  
  console.log('\n1. Loading app and starting trial...');
  await page.goto('http://localhost:1420');
  
  // Start trial
  const trial = await page.waitForSelector('button:has-text("Start Trial")', { timeout: 5000 }).catch(() => null);
  if (trial) {
    await trial.click();
    console.log('   ✓ Started trial');
  }
  
  await page.waitForTimeout(2000);
  
  // Navigate to Folders
  console.log('\n2. Navigating to Folders page...');
  await page.click('a:has-text("Folders")');
  await page.waitForTimeout(2000);
  
  // Check if folders are displayed
  console.log('\n3. Checking for folders in the list...');
  
  const folderList = await page.evaluate(() => {
    const body = document.body.innerText;
    return {
      hasEmptyMessage: body.includes('No folders added yet'),
      pageText: body.substring(0, 2000)
    };
  });
  
  if (folderList.hasEmptyMessage) {
    console.log('   ⚠ Still showing "No folders added yet" message');
  } else {
    console.log('   ✓ Empty message is gone!');
  }
  
  // Look for folder items
  const folders = await page.$$eval('[class*="hover:bg-gray"], [class*="cursor-pointer"], .folder-item', elements => {
    return elements
      .map(el => el.textContent.trim())
      .filter(text => text && !text.includes('Folders') && !text.includes('No folders') && text.length > 5)
      .slice(0, 5);
  });
  
  console.log(`\n4. Folders found in list: ${folders.length}`);
  folders.forEach(f => console.log(`   - ${f.substring(0, 50)}`));
  
  // Try clicking on a folder
  if (folders.length > 0) {
    console.log('\n5. Trying to click on first folder...');
    
    // Find and click the first folder item
    const folderItem = await page.$('[class*="hover:bg-gray"]:has-text("usenet_test"), [class*="cursor-pointer"]:has-text("tmp")').catch(() => null);
    
    if (folderItem) {
      await folderItem.click();
      console.log('   ✓ Clicked on folder');
      await page.waitForTimeout(2000);
      
      // Check for tabs
      console.log('\n6. Checking for tabs...');
      const tabs = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        return buttons
          .map(b => b.textContent.trim())
          .filter(text => ['Overview', 'Files', 'Segments', 'Shares', 'Actions'].includes(text));
      });
      
      if (tabs.length > 0) {
        console.log(`   ✓ TABS FOUND: ${tabs.join(', ')}`);
        
        // Test each tab
        for (const tabName of tabs) {
          const tab = await page.$(`button:text-is("${tabName}")`);
          if (tab) {
            await tab.click();
            console.log(`   ✓ Clicked ${tabName} tab`);
            await page.waitForTimeout(500);
            
            // Get tab content
            const content = await page.evaluate(() => {
              const main = document.querySelector('[role="tabpanel"], .tab-content, main > div > div');
              return main ? main.textContent.substring(0, 100) : '';
            });
            
            if (content) {
              console.log(`     Content preview: ${content}`);
            }
          }
        }
      } else {
        console.log('   ✗ No tabs found');
      }
    } else {
      console.log('   ✗ Could not find clickable folder item');
    }
  }
  
  // Take screenshot
  await page.screenshot({ path: '/tmp/folders_after_fix.png', fullPage: true });
  console.log('\n7. Screenshot saved to /tmp/folders_after_fix.png');
  
  // Get current page structure for debugging
  const structure = await page.evaluate(() => {
    const sidebar = document.querySelector('.w-80');
    const main = document.querySelector('main > div > .flex-1');
    
    return {
      sidebarContent: sidebar ? sidebar.innerText.substring(0, 500) : 'No sidebar',
      mainContent: main ? main.innerText.substring(0, 500) : 'No main content'
    };
  });
  
  console.log('\n8. Page structure:');
  console.log('   Sidebar:', structure.sidebarContent.replace(/\n/g, ' ').substring(0, 100));
  console.log('   Main:', structure.mainContent.replace(/\n/g, ' ').substring(0, 100));
  
  await browser.close();
  
  console.log('\n' + '='.repeat(60));
  console.log('TEST COMPLETE');
  console.log('='.repeat(60));
})().catch(console.error);