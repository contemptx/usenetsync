const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  // Monitor console and network
  page.on('console', msg => {
    if (msg.type() === 'error' || msg.type() === 'warning') {
      console.log(`Browser ${msg.type()}:`, msg.text());
    }
  });
  
  page.on('request', request => {
    if (request.url().includes('/api/')) {
      console.log(`→ API Request: ${request.method()} ${request.url().replace('http://localhost:8000', '')}`);
      if (request.postData()) {
        console.log(`  Body:`, request.postData());
      }
    }
  });
  
  page.on('response', response => {
    if (response.url().includes('/api/') && response.status() !== 200) {
      console.log(`← API Response: ${response.status()} ${response.url().replace('http://localhost:8000', '')}`);
    }
  });
  
  console.log('1. Loading app...');
  await page.goto('http://localhost:1420');
  
  // Start trial
  const trial = await page.$('button:has-text("Start Trial")');
  if (trial) {
    await trial.click();
    console.log('2. Started trial');
  }
  await page.waitForTimeout(2000);
  
  // Navigate to Folders
  const folders = await page.$('a:has-text("Folders")');
  if (folders) {
    await folders.click();
    console.log('3. Navigated to Folders');
  }
  await page.waitForTimeout(2000);
  
  // Find the Add Folder button by its title attribute
  console.log('\n4. Looking for Add Folder button...');
  const addButton = await page.$('button[title="Add Folder"]');
  
  if (addButton) {
    console.log('   ✓ Found Add Folder button');
    
    // Click it
    console.log('5. Clicking Add Folder button...');
    await addButton.click();
    await page.waitForTimeout(3000);
    
    // Check what happened
    const afterClick = await page.evaluate(() => {
      // Check for any dialogs
      const dialog = document.querySelector('[role="dialog"], .modal, [class*="dialog"], [class*="Dialog"]');
      const fileInput = document.querySelector('input[type="file"]');
      const errorMessages = Array.from(document.querySelectorAll('.error, [class*="error"]')).map(e => e.textContent);
      
      return {
        hasDialog: !!dialog,
        dialogContent: dialog ? dialog.textContent.substring(0, 200) : null,
        hasFileInput: !!fileInput,
        fileInputVisible: fileInput ? window.getComputedStyle(fileInput).display !== 'none' : false,
        errors: errorMessages,
        bodyText: document.body.innerText.substring(0, 100)
      };
    });
    
    console.log('\n6. After clicking Add Folder:');
    console.log('   Has dialog:', afterClick.hasDialog);
    console.log('   Dialog content:', afterClick.dialogContent);
    console.log('   Has file input:', afterClick.hasFileInput);
    console.log('   File input visible:', afterClick.fileInputVisible);
    console.log('   Errors:', afterClick.errors);
    
    // Try to programmatically add a folder path
    console.log('\n7. Trying to add a test folder via API...');
    const apiResponse = await page.evaluate(async () => {
      const response = await fetch('http://localhost:8000/api/v1/add_folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: '/workspace/test_folder' })
      });
      return {
        status: response.status,
        data: await response.json()
      };
    });
    
    console.log('   API Response:', apiResponse);
    
    if (apiResponse.status === 200 && apiResponse.data.success) {
      console.log('   ✓ Folder added successfully via API');
      console.log('   Folder ID:', apiResponse.data.folder_id);
      
      // Refresh the page to see if the folder appears
      await page.reload();
      await page.waitForTimeout(2000);
      
      // Check if folder now appears in list
      const folderList = await page.evaluate(() => {
        const text = document.body.innerText;
        return {
          hasTestFolder: text.includes('test_folder'),
          stillShowsEmpty: text.includes('No folders added yet')
        };
      });
      
      console.log('\n8. After adding folder:');
      console.log('   Shows test_folder:', folderList.hasTestFolder);
      console.log('   Still shows empty message:', folderList.stillShowsEmpty);
    }
    
  } else {
    console.log('   ✗ Add Folder button not found');
  }
  
  // Take final screenshot
  await page.screenshot({ path: '/tmp/after_add_folder.png', fullPage: true });
  console.log('\n9. Screenshot saved to /tmp/after_add_folder.png');
  
  await browser.close();
})().catch(console.error);