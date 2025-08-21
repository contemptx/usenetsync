const { chromium } = require('playwright');

async function testCompleteGUI() {
  console.log('='*70);
  console.log(' TESTING COMPLETE GUI FUNCTIONALITY');
  console.log('='*70);
  
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  try {
    // 1. Navigate to the app
    console.log('\n1. Loading application...');
    await page.goto('http://localhost:1420', { waitUntil: 'networkidle' });
    
    // Check if we're on license page
    const licenseButton = await page.$('button:has-text("Start Trial")');
    if (licenseButton) {
      console.log('   - Starting trial...');
      await licenseButton.click();
      await page.waitForTimeout(1000);
    }
    
    // 2. Navigate to Folders page
    console.log('\n2. Navigating to Folders page...');
    const foldersLink = await page.$('a[href="/folders"]');
    if (foldersLink) {
      await foldersLink.click();
      await page.waitForTimeout(1000);
    } else {
      // Try button navigation
      const foldersButton = await page.$('button:has-text("Folders")');
      if (foldersButton) {
        await foldersButton.click();
        await page.waitForTimeout(1000);
      }
    }
    
    // 3. Check current folders
    console.log('\n3. Checking existing folders...');
    const folderItems = await page.$$('.folder-item, [class*="folder"], tr');
    console.log(`   - Found ${folderItems.length} folder items`);
    
    // 4. Test Add Folder functionality
    console.log('\n4. Testing Add Folder...');
    const addButton = await page.$('button:has-text("Add Folder"), button:has-text("Add"), button[title*="Add"]');
    if (addButton) {
      console.log('   - Found Add Folder button');
      
      // Check if clicking opens a dialog or file input
      const [fileChooser] = await Promise.all([
        page.waitForEvent('filechooser', { timeout: 1000 }).catch(() => null),
        addButton.click()
      ]);
      
      if (fileChooser) {
        console.log('   - File chooser opened (would select folder in real scenario)');
      } else {
        console.log('   - Button clicked (may need file input simulation)');
      }
    } else {
      console.log('   ✗ Add Folder button not found');
    }
    
    // 5. Check folder details view
    console.log('\n5. Checking folder details...');
    const firstFolder = await page.$('.folder-item:first-child, tr:first-child');
    if (firstFolder) {
      await firstFolder.click();
      await page.waitForTimeout(1000);
      
      // Check for tabs
      const tabs = await page.$$('button[role="tab"], .tab-button, button:has-text("Overview"), button:has-text("Files")');
      console.log(`   - Found ${tabs.length} tabs`);
      
      // Test each tab
      const tabNames = ['Overview', 'Files', 'Segments', 'Shares', 'Actions'];
      for (const tabName of tabNames) {
        const tab = await page.$(`button:has-text("${tabName}")`);
        if (tab) {
          console.log(`   - Testing ${tabName} tab...`);
          await tab.click();
          await page.waitForTimeout(500);
          
          // Check content in each tab
          const content = await page.textContent('main, .tab-content, [role="tabpanel"]');
          if (content && content.length > 50) {
            console.log(`     ✓ ${tabName} tab has content`);
          }
        }
      }
    }
    
    // 6. Test Actions
    console.log('\n6. Testing folder actions...');
    const actionButtons = await page.$$('button:has-text("Index"), button:has-text("Segment"), button:has-text("Upload"), button:has-text("Share")');
    console.log(`   - Found ${actionButtons.length} action buttons`);
    
    // 7. Check for share creation
    console.log('\n7. Testing share creation...');
    const shareButton = await page.$('button:has-text("Create Share"), button:has-text("Share")');
    if (shareButton) {
      console.log('   - Found Share button');
      await shareButton.click();
      await page.waitForTimeout(500);
      
      // Check for share dialog
      const shareDialog = await page.$('dialog, [role="dialog"], .modal');
      if (shareDialog) {
        console.log('   ✓ Share dialog opened');
        
        // Check share options
        const shareTypes = await page.$$('input[type="radio"], button:has-text("Public"), button:has-text("Private")');
        console.log(`   - Found ${shareTypes.length} share type options`);
      }
    }
    
    // 8. Get page structure for debugging
    console.log('\n8. Page structure analysis...');
    const mainContent = await page.$eval('main, #root, body', el => {
      const structure = {
        tagName: el.tagName,
        classes: el.className,
        childCount: el.children.length,
        hasButtons: el.querySelectorAll('button').length,
        hasForms: el.querySelectorAll('form').length,
        hasTables: el.querySelectorAll('table').length,
        hasLists: el.querySelectorAll('ul, ol').length
      };
      return structure;
    });
    console.log('   Page structure:', JSON.stringify(mainContent, null, 2));
    
    console.log('\n' + '='*70);
    console.log(' GUI TEST COMPLETE');
    console.log('='*70);
    
  } catch (error) {
    console.error('Error during testing:', error.message);
  } finally {
    await browser.close();
  }
}

testCompleteGUI().catch(console.error);