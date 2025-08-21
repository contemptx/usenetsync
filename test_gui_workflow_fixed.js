const { chromium } = require('playwright');

async function testGUIWorkflow() {
  console.log('='.repeat(70));
  console.log(' GUI WORKFLOW TEST - FIXED VERSION');
  console.log('='.repeat(70));

  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  try {
    // 1. Setup and navigation
    console.log('\n1. SETUP');
    await page.goto('http://localhost:1420');
    
    // Start trial
    const trial = await page.$('button:has-text("Start Trial")');
    if (trial) {
      await trial.click();
      console.log('   ✓ Trial started');
    }
    await page.waitForTimeout(2000);
    
    // Navigate to Folders
    await page.click('a:has-text("Folders")');
    await page.waitForTimeout(3000); // Wait longer for folders to load
    console.log('   ✓ On Folders page');

    // 2. Check current folders
    console.log('\n2. CURRENT FOLDERS');
    const existingFolders = await page.evaluate(() => {
      const body = document.body.innerText;
      const sidebar = document.querySelector('.w-80');
      
      // Count folder items (excluding headers)
      let folderCount = 0;
      if (sidebar) {
        const divs = sidebar.querySelectorAll('div');
        divs.forEach(div => {
          const text = div.textContent || '';
          if (text.includes('/') && !text.includes('Folders') && !text.includes('SQLite')) {
            folderCount++;
          }
        });
      }
      
      return {
        hasEmptyMessage: body.includes('No folders added yet'),
        folderCount: folderCount
      };
    });
    
    console.log(`   Folders in list: ${existingFolders.folderCount}`);
    console.log(`   Shows empty message: ${existingFolders.hasEmptyMessage}`);

    // 3. Add folder via API
    console.log('\n3. ADDING FOLDER');
    const addResult = await page.evaluate(async () => {
      const res = await fetch('http://localhost:8000/api/v1/add_folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          path: '/workspace/test_workflow_folder', 
          name: 'Test Workflow' 
        })
      });
      return await res.json();
    });
    
    if (addResult.success) {
      console.log('   ✓ Folder added');
      console.log(`   ID: ${addResult.folder_id}`);
      console.log(`   Files: ${addResult.files_indexed}`);
      
      // Navigate away and back to refresh
      await page.click('a:has-text("Dashboard")');
      await page.waitForTimeout(1000);
      await page.click('a:has-text("Folders")');
      await page.waitForTimeout(3000);
      console.log('   ✓ Page refreshed');
    }

    // 4. Verify folder appears
    console.log('\n4. VERIFYING FOLDER APPEARS');
    const updatedFolders = await page.evaluate(() => {
      const sidebar = document.querySelector('.w-80');
      if (!sidebar) return { found: false, folders: [] };
      
      const folders = [];
      const divs = sidebar.querySelectorAll('div');
      divs.forEach(div => {
        const text = div.textContent || '';
        if (text.includes('test_workflow') || text.includes('Test Workflow')) {
          folders.push(text.trim().substring(0, 100));
        }
      });
      
      return { found: folders.length > 0, folders };
    });
    
    if (updatedFolders.found) {
      console.log('   ✓ Folder found in list!');
      updatedFolders.folders.forEach(f => console.log(`     - ${f}`));
      
      // 5. Click on the folder
      console.log('\n5. SELECTING FOLDER');
      const clicked = await page.evaluate(() => {
        const sidebar = document.querySelector('.w-80');
        if (!sidebar) return false;
        
        const items = sidebar.querySelectorAll('div');
        for (let item of items) {
          if (item.textContent && item.textContent.includes('test_workflow')) {
            // Check if it's clickable
            const styles = window.getComputedStyle(item);
            if (styles.cursor === 'pointer' || item.className.includes('cursor-pointer')) {
              item.click();
              return true;
            }
          }
        }
        return false;
      });
      
      if (clicked) {
        console.log('   ✓ Folder clicked');
        await page.waitForTimeout(1000);
        
        // 6. Test tabs
        console.log('\n6. TESTING TABS');
        const tabs = ['overview', 'files', 'segments', 'shares', 'actions'];
        let tabsFound = 0;
        
        for (const tab of tabs) {
          const tabButton = await page.$(`button:has-text("${tab}")`);
          if (tabButton) {
            await tabButton.click();
            tabsFound++;
            console.log(`   ✓ ${tab} tab works`);
            await page.waitForTimeout(300);
          }
        }
        console.log(`   Total tabs found: ${tabsFound}/5`);
        
        // 7. Test segmentation
        console.log('\n7. TESTING SEGMENTATION');
        const segmentResult = await page.evaluate(async (folderId) => {
          const res = await fetch('http://localhost:8000/api/v1/process_folder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folderId })
          });
          return { status: res.status, data: await res.json() };
        }, addResult.folder_id);
        
        if (segmentResult.status === 200 && segmentResult.data.success) {
          console.log(`   ✓ Segmentation successful!`);
          console.log(`   Segments created: ${segmentResult.data.segments_created}`);
        } else {
          console.log(`   ✗ Segmentation failed: ${segmentResult.status}`);
        }
      }
    } else {
      console.log('   ✗ Folder not appearing in list');
      console.log('   This may be a refresh issue');
    }

    // 8. Final screenshot
    await page.screenshot({ path: '/tmp/gui_final_test.png', fullPage: true });
    console.log('\n✓ Screenshot saved to /tmp/gui_final_test.png');

  } catch (error) {
    console.error('\n✗ Error:', error.message);
    await page.screenshot({ path: '/tmp/gui_error.png' });
  } finally {
    await browser.close();
  }

  console.log('\n' + '='.repeat(70));
  console.log(' TEST COMPLETE');
  console.log('='.repeat(70));
}

testGUIWorkflow().catch(console.error);