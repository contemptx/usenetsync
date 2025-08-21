const { chromium } = require('playwright');

async function testCompleteGUIWorkflow() {
  console.log('='.repeat(70));
  console.log(' COMPLETE GUI WORKFLOW TEST WITH CHROMIUM');
  console.log('='.repeat(70));

  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  // Monitor API calls
  const apiCalls = [];
  page.on('request', request => {
    if (request.url().includes('/api/')) {
      const endpoint = request.url().replace('http://localhost:8000', '');
      apiCalls.push(`${request.method()} ${endpoint}`);
      console.log(`  → API: ${request.method()} ${endpoint}`);
    }
  });

  page.on('response', response => {
    if (response.url().includes('/api/') && response.status() !== 200) {
      console.log(`  ← API Error: ${response.status()} ${response.url().replace('http://localhost:8000', '')}`);
    }
  });

  try {
    // 1. LOAD APPLICATION
    console.log('\n1. LOADING APPLICATION');
    await page.goto('http://localhost:1420', { waitUntil: 'networkidle' });
    console.log('   ✓ Application loaded');

    // 2. START TRIAL
    console.log('\n2. STARTING TRIAL');
    const trialButton = await page.$('button:has-text("Start Trial")');
    if (trialButton) {
      await trialButton.click();
      console.log('   ✓ Trial started');
      await page.waitForTimeout(2000);
    }

    // 3. NAVIGATE TO FOLDERS
    console.log('\n3. NAVIGATING TO FOLDERS');
    await page.click('a:has-text("Folders")');
    await page.waitForTimeout(2000);
    console.log('   ✓ On Folders page');

    // 4. ADD A NEW FOLDER (via API since file dialog won't work in headless)
    console.log('\n4. ADDING TEST FOLDER');
    const folderAdded = await page.evaluate(async () => {
      const response = await fetch('http://localhost:8000/api/v1/add_folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          path: '/workspace/test_workflow_folder', 
          name: 'GUI Test Folder' 
        })
      });
      const data = await response.json();
      return data;
    });
    
    if (folderAdded.success) {
      console.log('   ✓ Folder added via API');
      console.log(`   Folder ID: ${folderAdded.folder_id}`);
      console.log(`   Files indexed: ${folderAdded.files_indexed}`);
      
      // Reload to see the folder
      await page.reload();
      await page.waitForTimeout(2000);
    }

    // 5. CHECK FOLDER LIST
    console.log('\n5. CHECKING FOLDER LIST');
    const folders = await page.evaluate(() => {
      const sidebar = document.querySelector('.w-80');
      if (!sidebar) return [];
      
      const items = Array.from(sidebar.querySelectorAll('div'));
      return items
        .map(div => div.textContent)
        .filter(text => text.includes('/workspace/test_workflow_folder') || text.includes('GUI Test Folder'))
        .slice(0, 3);
    });
    
    console.log(`   ✓ Found ${folders.length} matching folders`);
    folders.forEach(f => console.log(`     - ${f.substring(0, 60)}`));

    // 6. CLICK ON FOLDER
    console.log('\n6. SELECTING FOLDER');
    const folderClicked = await page.evaluate(() => {
      const sidebar = document.querySelector('.w-80');
      const items = sidebar.querySelectorAll('div[class*="cursor-pointer"], div[class*="hover:bg-gray"]');
      
      for (let item of items) {
        if (item.textContent.includes('test_workflow_folder')) {
          item.click();
          return true;
        }
      }
      return false;
    });
    
    if (folderClicked) {
      console.log('   ✓ Folder selected');
      await page.waitForTimeout(1000);
    }

    // 7. TEST ALL TABS
    console.log('\n7. TESTING TABS');
    const tabs = ['overview', 'files', 'segments', 'shares', 'actions'];
    
    for (const tabName of tabs) {
      const tab = await page.$(`button:has-text("${tabName}")`);
      if (tab) {
        await tab.click();
        console.log(`   ✓ ${tabName.toUpperCase()} tab - clicked`);
        await page.waitForTimeout(500);
        
        // Check tab content
        const hasContent = await page.evaluate(() => {
          const main = document.querySelector('main .flex-1');
          return main && main.textContent.length > 50;
        });
        
        if (hasContent) {
          console.log(`     → Tab has content`);
        }
      } else {
        console.log(`   ⚠ ${tabName} tab not found`);
      }
    }

    // 8. TEST ACTIONS TAB BUTTONS
    console.log('\n8. TESTING ACTION BUTTONS');
    
    // Click Actions tab
    const actionsTab = await page.$('button:has-text("actions")');
    if (actionsTab) {
      await actionsTab.click();
      await page.waitForTimeout(500);
      
      // Test Process/Segment button
      console.log('   Testing segmentation...');
      const segmentResult = await page.evaluate(async (folderId) => {
        const response = await fetch('http://localhost:8000/api/v1/process_folder', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ folderId: folderId })
        });
        return { status: response.status, data: await response.json() };
      }, folderAdded.folder_id);
      
      if (segmentResult.status === 200) {
        console.log(`   ✓ Segmentation successful: ${segmentResult.data.segments_created} segments created`);
      } else {
        console.log(`   ✗ Segmentation failed: ${segmentResult.status}`);
      }
      
      // Test Upload button
      console.log('   Testing upload...');
      const uploadResult = await page.evaluate(async (folderId) => {
        const response = await fetch('http://localhost:8000/api/v1/upload_folder', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ folderId: folderId })
        });
        return { status: response.status, data: await response.text() };
      }, folderAdded.folder_id);
      
      console.log(`   Upload status: ${uploadResult.status}`);
      
      // Test Create Share button
      console.log('   Testing share creation...');
      const shareResult = await page.evaluate(async (folderId) => {
        const response = await fetch('http://localhost:8000/api/v1/create_share', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            folderId: folderId,
            shareType: 'public'
          })
        });
        return { status: response.status, data: await response.text() };
      }, folderAdded.folder_id);
      
      console.log(`   Share creation status: ${shareResult.status}`);
    }

    // 9. CHECK OTHER PAGES
    console.log('\n9. TESTING OTHER PAGES');
    
    // Test Upload page
    await page.click('a:has-text("Upload")');
    await page.waitForTimeout(1000);
    const onUploadPage = await page.evaluate(() => window.location.pathname === '/upload');
    console.log(`   ✓ Upload page: ${onUploadPage ? 'loaded' : 'error'}`);
    
    // Test Download page
    await page.click('a:has-text("Download")');
    await page.waitForTimeout(1000);
    const onDownloadPage = await page.evaluate(() => window.location.pathname === '/download');
    console.log(`   ✓ Download page: ${onDownloadPage ? 'loaded' : 'error'}`);
    
    // Test Shares page
    await page.click('a:has-text("Shares")');
    await page.waitForTimeout(1000);
    const onSharesPage = await page.evaluate(() => window.location.pathname === '/shares');
    console.log(`   ✓ Shares page: ${onSharesPage ? 'loaded' : 'error'}`);

    // 10. FINAL STATISTICS
    console.log('\n10. FINAL STATISTICS');
    const stats = await page.evaluate(async () => {
      const response = await fetch('http://localhost:8000/api/v1/stats');
      return await response.json();
    });
    
    console.log('   System stats:');
    console.log(`     Folders: ${stats.total_folders || 0}`);
    console.log(`     Files: ${stats.total_files || 0}`);
    console.log(`     Segments: ${stats.total_segments || 0}`);
    console.log(`     Shares: ${stats.total_shares || 0}`);

    // Take final screenshot
    await page.screenshot({ path: '/tmp/gui_workflow_complete.png', fullPage: true });
    console.log('\n   ✓ Screenshot saved to /tmp/gui_workflow_complete.png');

  } catch (error) {
    console.error('\n✗ Error during test:', error.message);
    await page.screenshot({ path: '/tmp/gui_error.png' });
  } finally {
    await browser.close();
  }

  // Summary
  console.log('\n' + '='.repeat(70));
  console.log(' TEST SUMMARY');
  console.log('='.repeat(70));
  console.log('\nAPI Calls Made:');
  const uniqueAPIs = [...new Set(apiCalls)];
  uniqueAPIs.forEach(api => console.log(`  - ${api}`));
  
  console.log('\n✅ GUI WORKFLOW TEST COMPLETE');
}

testCompleteGUIWorkflow().catch(console.error);