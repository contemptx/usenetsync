const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  console.log('1. Loading app and starting trial...');
  await page.goto('http://localhost:1420');
  
  // Start trial
  const trial = await page.waitForSelector('button:has-text("Start Trial")', { timeout: 5000 }).catch(() => null);
  if (trial) {
    await trial.click();
    console.log('   ✓ Started trial');
  }
  
  // Wait for navigation to be ready
  await page.waitForSelector('a:has-text("Folders")', { timeout: 5000 });
  
  // Navigate to Folders
  console.log('\n2. Navigating to Folders page...');
  await page.click('a:has-text("Folders")');
  
  // Wait for the Folders page to load - look for the "No folders" message or the Add button
  await page.waitForSelector('text=No folders added yet, button[title="Add Folder"], .lucide-folder-open', { timeout: 5000 }).catch(() => {});
  
  console.log('   ✓ On Folders page');
  
  // Try multiple selectors for the Add Folder button
  console.log('\n3. Finding Add Folder button...');
  
  const selectors = [
    'button[title="Add Folder"]',
    'button:has(.lucide-folder-open)',
    'button:has(svg):has-text("")', // Button with only SVG
    '.p-2.bg-primary',
    'button.bg-primary'
  ];
  
  let addButton = null;
  for (const selector of selectors) {
    addButton = await page.$(selector);
    if (addButton) {
      console.log(`   ✓ Found button with selector: ${selector}`);
      break;
    }
  }
  
  if (addButton) {
    console.log('\n4. Clicking Add Folder button...');
    
    // Intercept the file dialog since we're in headless mode
    page.on('filechooser', async (fileChooser) => {
      console.log('   ✓ File chooser dialog opened');
      // In headless mode, we can't actually select a folder
      // But we know the dialog was triggered
    });
    
    await addButton.click();
    console.log('   ✓ Clicked Add Folder button');
    
    // Wait a bit to see if anything happens
    await page.waitForTimeout(2000);
    
    // Since file dialog won't work in headless, test the API directly
    console.log('\n5. Testing folder addition via API...');
    
    const apiTest = await page.evaluate(async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/add_folder', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path: '/workspace/test_folder', name: 'Test Folder' })
        });
        const data = await response.json();
        return { success: true, status: response.status, data };
      } catch (error) {
        return { success: false, error: error.message };
      }
    });
    
    console.log('   API Result:', JSON.stringify(apiTest, null, 2));
    
    if (apiTest.success && apiTest.data.success) {
      // Reload to see the new folder
      console.log('\n6. Reloading to see new folder...');
      await page.reload();
      await page.waitForTimeout(2000);
      
      // Check if folder appears
      const pageContent = await page.evaluate(() => ({
        hasEmptyMessage: document.body.innerText.includes('No folders added yet'),
        hasTestFolder: document.body.innerText.includes('test_folder') || document.body.innerText.includes('Test Folder'),
        folderElements: Array.from(document.querySelectorAll('[class*="folder"]')).map(el => el.textContent.substring(0, 50))
      }));
      
      console.log('\n7. Page state after adding folder:');
      console.log('   Still shows empty:', pageContent.hasEmptyMessage);
      console.log('   Shows test folder:', pageContent.hasTestFolder);
      console.log('   Folder elements found:', pageContent.folderElements.length);
      
      // Test the tabs
      console.log('\n8. Testing tabs (if folder selected)...');
      
      // Try to click on a folder if it exists
      const folderItem = await page.$('[class*="cursor-pointer"]:has-text("test_folder"), [class*="cursor-pointer"]:has-text("Test Folder")').catch(() => null);
      
      if (folderItem) {
        await folderItem.click();
        console.log('   ✓ Clicked on folder');
        await page.waitForTimeout(1000);
        
        // Now check for tabs
        const tabs = await page.evaluate(() => {
          const buttons = Array.from(document.querySelectorAll('button'));
          return buttons
            .map(b => b.textContent.trim())
            .filter(text => ['Overview', 'Files', 'Segments', 'Shares', 'Actions'].includes(text));
        });
        
        console.log('   Tabs found:', tabs);
        
        // Test clicking each tab
        for (const tabName of tabs) {
          const tab = await page.$(`button:text-is("${tabName}")`);
          if (tab) {
            await tab.click();
            console.log(`   ✓ Clicked ${tabName} tab`);
            await page.waitForTimeout(500);
          }
        }
      } else {
        console.log('   ✗ No folder item found to click');
      }
    }
    
  } else {
    console.log('   ✗ Add Folder button not found with any selector');
    
    // Debug: Get all buttons on the page
    const buttons = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('button')).map(b => ({
        text: b.textContent.trim(),
        title: b.title,
        classes: b.className,
        hasIcon: b.querySelector('svg') !== null
      }));
    });
    
    console.log('\n   Debug - All buttons on page:');
    buttons.forEach(b => {
      if (b.hasIcon || b.title) {
        console.log(`   - Text: "${b.text}", Title: "${b.title}", Has Icon: ${b.hasIcon}`);
      }
    });
  }
  
  // Final screenshot
  await page.screenshot({ path: '/tmp/folders_final.png', fullPage: true });
  console.log('\n9. Final screenshot saved to /tmp/folders_final.png');
  
  await browser.close();
})().catch(console.error);