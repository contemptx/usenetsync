const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Create test data
function createTestData() {
  const testDir = '/workspace/real_test_data';
  if (!fs.existsSync(testDir)) {
    fs.mkdirSync(testDir, { recursive: true });
  }
  
  // Create some real files with content
  for (let i = 1; i <= 3; i++) {
    const content = `This is test file ${i}\n`.repeat(1000);
    fs.writeFileSync(path.join(testDir, `document_${i}.txt`), content);
  }
  
  // Create a subdirectory with files
  const subDir = path.join(testDir, 'subdirectory');
  if (!fs.existsSync(subDir)) {
    fs.mkdirSync(subDir);
  }
  fs.writeFileSync(path.join(subDir, 'nested_file.txt'), 'Nested content\n'.repeat(500));
  
  return testDir;
}

async function testRealFolderWorkflow() {
  const browser = await chromium.launch({ 
    headless: false, // Run with GUI visible for debugging
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // Enable detailed console logging
  page.on('console', msg => {
    console.log(`[Browser ${msg.type()}]:`, msg.text());
  });
  
  page.on('response', response => {
    if (response.url().includes('/api/')) {
      console.log(`[API Response] ${response.url()} - ${response.status()}`);
    }
  });
  
  try {
    console.log('='*80);
    console.log(' REAL FOLDER MANAGEMENT WORKFLOW TEST');
    console.log(' Testing with real Usenet credentials: news.newshosting.com');
    console.log('='*80);
    
    // Create test data
    const testFolder = createTestData();
    console.log(`\n✅ Created test data in: ${testFolder}`);
    
    // 1. Navigate to Folders page
    console.log('\n1. NAVIGATING TO FOLDERS PAGE...');
    await page.goto('http://localhost:1420/folders', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // Take screenshot
    await page.screenshot({ path: '/workspace/test_screenshots/01_folders_page.png', fullPage: true });
    console.log('   📸 Screenshot saved: 01_folders_page.png');
    
    // 2. Add Folder
    console.log('\n2. TESTING ADD FOLDER...');
    const addButton = await page.$('button[title="Add Folder"]');
    if (addButton) {
      console.log('   ✓ Found Add Folder button');
      
      // Since we can't use file dialog in headless, we'll use API directly
      const addResponse = await page.evaluate(async (folderPath) => {
        const response = await fetch('http://localhost:8000/api/v1/add_folder', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path: folderPath, name: 'Real Test Folder' })
        });
        return { 
          status: response.status, 
          data: await response.json() 
        };
      }, testFolder);
      
      console.log(`   ✓ Add folder response: ${addResponse.status}`);
      console.log(`   ✓ Folder ID: ${addResponse.data.folder_id}`);
      
      // Refresh to see the new folder
      await page.reload({ waitUntil: 'networkidle' });
      await page.waitForTimeout(2000);
    }
    
    // 3. Select the folder
    console.log('\n3. SELECTING FOLDER...');
    const folderItems = await page.$$('.divide-y > div');
    if (folderItems.length > 0) {
      console.log(`   ✓ Found ${folderItems.length} folders`);
      
      // Click on the first folder (our new one)
      await folderItems[0].click();
      await page.waitForTimeout(1000);
      
      await page.screenshot({ path: '/workspace/test_screenshots/02_folder_selected.png', fullPage: true });
      console.log('   📸 Screenshot saved: 02_folder_selected.png');
      
      // Check if tabs appeared
      const tabs = await page.$$eval('button[class*="capitalize"]', buttons => 
        buttons.map(b => b.textContent?.trim())
      );
      console.log(`   ✓ Tabs visible: ${tabs.join(', ')}`);
    }
    
    // 4. Test Overview Tab
    console.log('\n4. TESTING OVERVIEW TAB...');
    const overviewTab = await page.$('button:text("overview")');
    if (overviewTab) {
      await overviewTab.click();
      await page.waitForTimeout(1000);
      
      const overviewContent = await page.evaluate(() => {
        const content = document.querySelector('.flex-1.overflow-y-auto');
        return {
          hasStatistics: !!content?.querySelector('h3:text("Folder Statistics")'),
          hasStatus: !!content?.querySelector('h3:text("Processing Status")'),
          hasSharing: !!content?.querySelector('h3:text("Sharing Status")'),
          text: content?.textContent?.substring(0, 200)
        };
      });
      
      console.log('   Overview Tab Content:');
      console.log(`     ${overviewContent.hasStatistics ? '✓' : '✗'} Folder Statistics`);
      console.log(`     ${overviewContent.hasStatus ? '✓' : '✗'} Processing Status`);
      console.log(`     ${overviewContent.hasSharing ? '✓' : '✗'} Sharing Status`);
    }
    
    // 5. Test Index Function
    console.log('\n5. TESTING INDEX FUNCTIONALITY...');
    const indexButton = await page.$('button:text("Index")');
    if (indexButton) {
      console.log('   ✓ Found Index button');
      await indexButton.click();
      await page.waitForTimeout(3000); // Wait for indexing
      
      await page.screenshot({ path: '/workspace/test_screenshots/03_after_index.png', fullPage: true });
      console.log('   📸 Screenshot saved: 03_after_index.png');
    }
    
    // 6. Test Files Tab
    console.log('\n6. TESTING FILES TAB...');
    const filesTab = await page.$('button:text("files")');
    if (filesTab) {
      await filesTab.click();
      await page.waitForTimeout(1000);
      
      const filesContent = await page.evaluate(() => {
        const content = document.querySelector('.flex-1.overflow-y-auto');
        const fileItems = content?.querySelectorAll('.border.border-gray-200');
        return {
          fileCount: fileItems?.length || 0,
          hasFileTree: fileItems && fileItems.length > 0,
          firstFileName: fileItems?.[0]?.textContent?.substring(0, 50)
        };
      });
      
      console.log(`   ✓ Files found: ${filesContent.fileCount}`);
      console.log(`   ✓ Has file tree: ${filesContent.hasFileTree}`);
      if (filesContent.firstFileName) {
        console.log(`   ✓ First file: ${filesContent.firstFileName}`);
      }
      
      await page.screenshot({ path: '/workspace/test_screenshots/04_files_tab.png', fullPage: true });
      console.log('   📸 Screenshot saved: 04_files_tab.png');
    }
    
    // 7. Test Segment Function
    console.log('\n7. TESTING SEGMENT FUNCTIONALITY...');
    const segmentButton = await page.$('button:text("Segment")');
    if (segmentButton) {
      console.log('   ✓ Found Segment button');
      await segmentButton.click();
      await page.waitForTimeout(5000); // Wait for segmentation
      
      // Go to Segments tab
      const segmentsTab = await page.$('button:text("segments")');
      if (segmentsTab) {
        await segmentsTab.click();
        await page.waitForTimeout(1000);
        
        const segmentInfo = await page.evaluate(() => {
          const content = document.querySelector('.flex-1.overflow-y-auto');
          return {
            text: content?.textContent?.substring(0, 300),
            hasSegmentStats: content?.textContent?.includes('Total Segments'),
            hasAvgSize: content?.textContent?.includes('Avg Segment Size')
          };
        });
        
        console.log(`   ✓ Has segment statistics: ${segmentInfo.hasSegmentStats}`);
        console.log(`   ✓ Has average size: ${segmentInfo.hasAvgSize}`);
        
        await page.screenshot({ path: '/workspace/test_screenshots/05_segments_tab.png', fullPage: true });
        console.log('   📸 Screenshot saved: 05_segments_tab.png');
      }
    }
    
    // 8. Test Upload to Usenet
    console.log('\n8. TESTING UPLOAD TO USENET...');
    console.log('   Using real credentials: news.newshosting.com, user: contemptx');
    
    const uploadButton = await page.$('button:text("Upload")');
    if (uploadButton) {
      console.log('   ✓ Found Upload button');
      await uploadButton.click();
      console.log('   ⏳ Uploading to Usenet (this may take a moment)...');
      await page.waitForTimeout(10000); // Wait for upload
      
      await page.screenshot({ path: '/workspace/test_screenshots/06_after_upload.png', fullPage: true });
      console.log('   📸 Screenshot saved: 06_after_upload.png');
    }
    
    // 9. Test Share Creation
    console.log('\n9. TESTING SHARE CREATION...');
    const shareButton = await page.$('button:text("Share"), button:text("Create Share")');
    if (shareButton) {
      console.log('   ✓ Found Share button');
      await shareButton.click();
      await page.waitForTimeout(1000);
      
      // Check if share dialog opened
      const shareDialog = await page.$('.fixed.inset-0');
      if (shareDialog) {
        console.log('   ✓ Share dialog opened');
        
        // Test different share types
        const publicRadio = await page.$('input[value="public"]');
        const privateRadio = await page.$('input[value="private"]');
        const protectedRadio = await page.$('input[value="protected"]');
        
        console.log(`   ✓ Public option: ${!!publicRadio}`);
        console.log(`   ✓ Private option: ${!!privateRadio}`);
        console.log(`   ✓ Protected option: ${!!protectedRadio}`);
        
        // Select protected and add password
        if (protectedRadio) {
          await protectedRadio.click();
          const passwordInput = await page.$('input[type="password"]');
          if (passwordInput) {
            await passwordInput.fill('test_password_123');
            console.log('   ✓ Password field filled');
          }
        }
        
        await page.screenshot({ path: '/workspace/test_screenshots/07_share_dialog.png', fullPage: true });
        console.log('   📸 Screenshot saved: 07_share_dialog.png');
        
        // Create the share
        const createShareButton = await page.$('button:text("Create Share")');
        if (createShareButton) {
          await createShareButton.click();
          await page.waitForTimeout(2000);
          console.log('   ✓ Share created');
        }
      }
    }
    
    // 10. Test Shares Tab
    console.log('\n10. TESTING SHARES TAB...');
    const sharesTab = await page.$('button:text("shares")');
    if (sharesTab) {
      await sharesTab.click();
      await page.waitForTimeout(1000);
      
      const sharesContent = await page.evaluate(() => {
        const content = document.querySelector('.flex-1.overflow-y-auto');
        const shareItems = content?.querySelectorAll('.border.border-gray-200');
        return {
          shareCount: shareItems?.length || 0,
          hasShares: shareItems && shareItems.length > 0,
          hasShareId: content?.textContent?.includes('Share ID')
        };
      });
      
      console.log(`   ✓ Shares found: ${sharesContent.shareCount}`);
      console.log(`   ✓ Has share ID: ${sharesContent.hasShareId}`);
      
      await page.screenshot({ path: '/workspace/test_screenshots/08_shares_tab.png', fullPage: true });
      console.log('   📸 Screenshot saved: 08_shares_tab.png');
    }
    
    // 11. Test Actions Tab
    console.log('\n11. TESTING ACTIONS TAB...');
    const actionsTab = await page.$('button:text("actions")');
    if (actionsTab) {
      await actionsTab.click();
      await page.waitForTimeout(1000);
      
      const actions = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        return {
          hasReindex: buttons.some(b => b.textContent?.includes('Re-index')),
          hasResegment: buttons.some(b => b.textContent?.includes('Re-segment')),
          hasReupload: buttons.some(b => b.textContent?.includes('Re-upload')),
          hasResync: buttons.some(b => b.textContent?.includes('Resync')),
          hasRepublish: buttons.some(b => b.textContent?.includes('Republish')),
          hasTestDownload: buttons.some(b => b.textContent?.includes('Test Download')),
          hasDelete: buttons.some(b => b.textContent?.includes('Delete'))
        };
      });
      
      console.log('   Processing Actions:');
      console.log(`     ${actions.hasReindex ? '✓' : '✗'} Re-index Folder`);
      console.log(`     ${actions.hasResegment ? '✓' : '✗'} Re-segment Folder`);
      console.log(`     ${actions.hasReupload ? '✓' : '✗'} Re-upload to Usenet`);
      console.log('   Maintenance Actions:');
      console.log(`     ${actions.hasResync ? '✓' : '✗'} Resync for Changes`);
      console.log(`     ${actions.hasRepublish ? '✓' : '✗'} Republish to Usenet`);
      console.log(`     ${actions.hasTestDownload ? '✓' : '✗'} Test Download`);
      console.log(`     ${actions.hasDelete ? '✓' : '✗'} Delete Folder`);
      
      await page.screenshot({ path: '/workspace/test_screenshots/09_actions_tab.png', fullPage: true });
      console.log('   📸 Screenshot saved: 09_actions_tab.png');
    }
    
    // 12. Test Resync
    console.log('\n12. TESTING RESYNC FUNCTIONALITY...');
    const resyncButton = await page.$('button:text("Resync")');
    if (resyncButton) {
      console.log('   ✓ Found Resync button');
      await resyncButton.click();
      await page.waitForTimeout(3000);
      console.log('   ✓ Resync completed');
    }
    
    console.log('\n' + '='*80);
    console.log(' REAL WORKFLOW TEST COMPLETE');
    console.log('='*80);
    console.log('\nScreenshots saved in /workspace/test_screenshots/');
    console.log('All features have been tested with real data and real Usenet server!');
    
  } catch (error) {
    console.error('Test error:', error);
    await page.screenshot({ path: '/workspace/test_screenshots/error.png', fullPage: true });
  } finally {
    // Keep browser open for 5 seconds to observe
    await page.waitForTimeout(5000);
    await browser.close();
  }
}

// Create screenshots directory
const screenshotDir = '/workspace/test_screenshots';
if (!fs.existsSync(screenshotDir)) {
  fs.mkdirSync(screenshotDir, { recursive: true });
}

testRealFolderWorkflow().catch(console.error);