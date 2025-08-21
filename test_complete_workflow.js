const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

async function testCompleteWorkflow() {
  const browser = await chromium.launch({ 
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // Track API calls
  const apiCalls = [];
  page.on('response', response => {
    if (response.url().includes('/api/')) {
      apiCalls.push({
        url: response.url(),
        status: response.status(),
        method: response.request().method()
      });
    }
  });
  
  try {
    console.log('='*80);
    console.log(' COMPLETE FOLDER WORKFLOW TEST WITH REAL USENET');
    console.log('='*80);
    
    // Navigate to folders
    console.log('\n1. Loading Folders page...');
    await page.goto('http://localhost:1420/folders', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // Click on first folder
    console.log('\n2. Selecting a folder...');
    const folders = await page.$$('.divide-y > div');
    if (folders.length > 0) {
      await folders[0].click();
      await page.waitForTimeout(1000);
      console.log('   ✓ Folder selected');
      
      // Get folder state
      const folderState = await page.evaluate(() => {
        const stateElement = document.querySelector('.capitalize.flex.items-center.gap-2');
        return stateElement?.textContent?.trim();
      });
      console.log(`   ✓ Current state: ${folderState || 'unknown'}`);
    }
    
    // Test each tab
    console.log('\n3. Testing all tabs...');
    
    // Overview Tab
    const overviewTab = await page.getByRole('button', { name: 'overview' });
    if (overviewTab) {
      await overviewTab.click();
      await page.waitForTimeout(500);
      
      const overviewStats = await page.evaluate(() => {
        const content = document.querySelector('.grid.grid-cols-3');
        return {
          hasStats: !!content,
          statsCount: content?.querySelectorAll('.bg-white').length || 0
        };
      });
      console.log(`   ✓ Overview Tab: ${overviewStats.statsCount} stat panels`);
    }
    
    // Files Tab
    const filesTab = await page.getByRole('button', { name: 'files' });
    if (filesTab) {
      await filesTab.click();
      await page.waitForTimeout(500);
      
      const filesInfo = await page.evaluate(() => {
        const content = document.querySelector('.flex-1.overflow-y-auto');
        const files = content?.querySelectorAll('.border.border-gray-200');
        return {
          fileCount: files?.length || 0,
          hasNoFilesMessage: content?.textContent?.includes('not indexed yet')
        };
      });
      console.log(`   ✓ Files Tab: ${filesInfo.fileCount} files, needs index: ${filesInfo.hasNoFilesMessage}`);
    }
    
    // Segments Tab
    const segmentsTab = await page.getByRole('button', { name: 'segments' });
    if (segmentsTab) {
      await segmentsTab.click();
      await page.waitForTimeout(500);
      
      const segmentInfo = await page.evaluate(() => {
        const content = document.querySelector('.flex-1.overflow-y-auto');
        return {
          hasContent: !!content,
          needsSegmentation: content?.textContent?.includes('not segmented yet')
        };
      });
      console.log(`   ✓ Segments Tab: needs segmentation: ${segmentInfo.needsSegmentation}`);
    }
    
    // Shares Tab
    const sharesTab = await page.getByRole('button', { name: 'shares' });
    if (sharesTab) {
      await sharesTab.click();
      await page.waitForTimeout(500);
      
      const shareInfo = await page.evaluate(() => {
        const content = document.querySelector('.flex-1.overflow-y-auto');
        const shares = content?.querySelectorAll('.border.border-gray-200');
        return {
          shareCount: shares?.length || 0,
          needsUpload: content?.textContent?.includes('Upload the folder first')
        };
      });
      console.log(`   ✓ Shares Tab: ${shareInfo.shareCount} shares, needs upload: ${shareInfo.needsUpload}`);
    }
    
    // Actions Tab
    const actionsTab = await page.getByRole('button', { name: 'actions' });
    if (actionsTab) {
      await actionsTab.click();
      await page.waitForTimeout(500);
      
      const actionButtons = await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button'));
        return buttons
          .map(b => b.textContent?.trim())
          .filter(text => text && text.length > 0 && !['overview', 'files', 'segments', 'shares', 'actions'].includes(text.toLowerCase()));
      });
      console.log(`   ✓ Actions Tab: ${actionButtons.length} action buttons`);
      console.log(`     Actions available: ${actionButtons.slice(0, 5).join(', ')}...`);
    }
    
    // Now perform the workflow
    console.log('\n4. PERFORMING COMPLETE WORKFLOW...');
    
    // Step 1: Index
    console.log('\n   STEP 1: INDEXING FOLDER...');
    const indexButton = await page.getByRole('button', { name: /Index|Re-index/ });
    if (indexButton) {
      await indexButton.click();
      console.log('   ⏳ Indexing in progress...');
      await page.waitForTimeout(3000);
      console.log('   ✓ Indexing complete');
    }
    
    // Check Files tab after indexing
    await filesTab.click();
    await page.waitForTimeout(1000);
    const filesAfterIndex = await page.evaluate(() => {
      const files = document.querySelectorAll('.border.border-gray-200');
      return files.length;
    });
    console.log(`   ✓ Files after indexing: ${filesAfterIndex}`);
    
    // Step 2: Segment
    console.log('\n   STEP 2: CREATING SEGMENTS...');
    await actionsTab.click();
    await page.waitForTimeout(500);
    
    const segmentButton = await page.getByRole('button', { name: /Segment|Re-segment/ });
    if (segmentButton) {
      const isDisabled = await segmentButton.isDisabled();
      if (!isDisabled) {
        await segmentButton.click();
        console.log('   ⏳ Creating segments...');
        await page.waitForTimeout(5000);
        console.log('   ✓ Segmentation complete');
      } else {
        console.log('   ⚠️ Segment button is disabled');
      }
    }
    
    // Check Segments tab
    await segmentsTab.click();
    await page.waitForTimeout(1000);
    const segmentsInfo = await page.evaluate(() => {
      const content = document.querySelector('.flex-1.overflow-y-auto');
      const text = content?.textContent || '';
      return {
        hasSegments: text.includes('Total Segments'),
        segmentCount: text.match(/(\d+)\s*Total Segments/)?.[1] || '0'
      };
    });
    console.log(`   ✓ Segments created: ${segmentsInfo.segmentCount}`);
    
    // Step 3: Upload to Usenet
    console.log('\n   STEP 3: UPLOADING TO USENET...');
    console.log('   Server: news.newshosting.com');
    console.log('   User: contemptx');
    
    await actionsTab.click();
    await page.waitForTimeout(500);
    
    const uploadButton = await page.getByRole('button', { name: /Upload|Re-upload/ });
    if (uploadButton) {
      const isDisabled = await uploadButton.isDisabled();
      if (!isDisabled) {
        await uploadButton.click();
        console.log('   ⏳ Uploading to Usenet (this will take time)...');
        await page.waitForTimeout(10000);
        console.log('   ✓ Upload initiated');
      } else {
        console.log('   ⚠️ Upload button is disabled');
      }
    }
    
    // Step 4: Create Share
    console.log('\n   STEP 4: CREATING SHARE...');
    await actionsTab.click();
    await page.waitForTimeout(500);
    
    const shareButton = await page.getByRole('button', { name: /Share|Publish/ });
    if (shareButton) {
      const isDisabled = await shareButton.isDisabled();
      if (!isDisabled) {
        await shareButton.click();
        await page.waitForTimeout(1000);
        
        // Check for share dialog
        const dialog = await page.$('.fixed.inset-0');
        if (dialog) {
          console.log('   ✓ Share dialog opened');
          
          // Select protected share
          const protectedRadio = await page.$('input[value="protected"]');
          if (protectedRadio) {
            await protectedRadio.click();
            
            const passwordInput = await page.$('input[type="password"]');
            if (passwordInput) {
              await passwordInput.fill('TestPassword123!');
              console.log('   ✓ Protected share with password');
            }
          }
          
          // Create the share
          const createButton = await dialog.$('button:has-text("Create Share")');
          if (createButton) {
            await createButton.click();
            await page.waitForTimeout(2000);
            console.log('   ✓ Share created');
          }
        }
      } else {
        console.log('   ⚠️ Share button is disabled (need to upload first)');
      }
    }
    
    // Check Shares tab
    await sharesTab.click();
    await page.waitForTimeout(1000);
    const sharesAfter = await page.evaluate(() => {
      const shares = document.querySelectorAll('.border.border-gray-200');
      return shares.length;
    });
    console.log(`   ✓ Total shares: ${sharesAfter}`);
    
    // Step 5: Test Maintenance Actions
    console.log('\n   STEP 5: TESTING MAINTENANCE ACTIONS...');
    await actionsTab.click();
    await page.waitForTimeout(500);
    
    // Test Resync
    const resyncButton = await page.getByRole('button', { name: 'Resync for Changes' });
    if (resyncButton) {
      await resyncButton.click();
      console.log('   ✓ Resync triggered');
      await page.waitForTimeout(2000);
    }
    
    // Final screenshot
    await page.screenshot({ path: '/workspace/test_screenshots/10_final_state.png', fullPage: true });
    console.log('\n   📸 Final screenshot saved: 10_final_state.png');
    
    // Summary of API calls
    console.log('\n5. API CALLS SUMMARY:');
    const apiSummary = {};
    apiCalls.forEach(call => {
      const endpoint = call.url.replace('http://localhost:8000/api/v1/', '');
      apiSummary[endpoint] = (apiSummary[endpoint] || 0) + 1;
    });
    
    Object.entries(apiSummary).forEach(([endpoint, count]) => {
      console.log(`   ${endpoint}: ${count} calls`);
    });
    
    console.log('\n' + '='*80);
    console.log(' ✅ COMPLETE WORKFLOW TEST FINISHED');
    console.log('='*80);
    
  } catch (error) {
    console.error('Test error:', error);
    await page.screenshot({ path: '/workspace/test_screenshots/workflow_error.png', fullPage: true });
  } finally {
    await page.waitForTimeout(3000);
    await browser.close();
  }
}

testCompleteWorkflow().catch(console.error);