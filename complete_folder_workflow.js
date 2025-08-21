const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Configuration
const FRONTEND_URL = 'http://localhost:1420';
const API_URL = 'http://localhost:8000/api/v1';
const OUTPUT_DIR = '/workspace/complete_workflow';
const VIDEO_DIR = '/workspace/complete_workflow_video';

// Ensure directories exist
[OUTPUT_DIR, VIDEO_DIR].forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

async function completeFolderWorkflow() {
  console.log('🔄 COMPLETING FULL FOLDER WORKFLOW');
  console.log('='*70);
  console.log('This will execute the COMPLETE workflow:');
  console.log('  1. Create and Add Folder');
  console.log('  2. Index ALL Files (with progress)');
  console.log('  3. Segment ALL Files (with progress)');
  console.log('  4. Upload to Usenet (with progress)');
  console.log('  5. Create Multiple Share Types');
  console.log('  6. Generate Share IDs');
  console.log('  7. Test Download Process');
  console.log('='*70);
  
  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    slowMo: 50
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: {
      dir: VIDEO_DIR,
      size: { width: 1920, height: 1080 }
    }
  });

  const page = await context.newPage();
  
  let screenshotCount = 0;
  const workflowResults = {
    timestamp: new Date().toISOString(),
    steps: [],
    shareIds: [],
    screenshots: []
  };
  
  async function screenshot(name, description) {
    screenshotCount++;
    const filename = `${OUTPUT_DIR}/${String(screenshotCount).padStart(3, '0')}_${name}.png`;
    await page.screenshot({ path: filename, fullPage: false });
    console.log(`  📸 ${screenshotCount}: ${description}`);
    workflowResults.screenshots.push({ number: screenshotCount, name, description, filename });
    return filename;
  }

  async function waitForOperation(operationName, maxWaitTime = 60000) {
    console.log(`  ⏳ Waiting for ${operationName}...`);
    const startTime = Date.now();
    let lastProgress = -1;
    
    while (Date.now() - startTime < maxWaitTime) {
      // Check for progress section
      const progressSection = await page.locator('text="Operation in Progress"').first();
      
      if (await progressSection.isVisible()) {
        const percentText = await page.locator('text=/\\d+%/').first();
        if (await percentText.isVisible()) {
          const text = await percentText.textContent();
          const match = text.match(/(\d+)%/);
          if (match) {
            const percent = parseInt(match[1]);
            if (percent !== lastProgress) {
              console.log(`    📊 ${operationName}: ${percent}%`);
              lastProgress = percent;
              
              // Capture key moments
              if (percent === 0 || percent === 25 || percent === 50 || percent === 75 || percent === 99 || percent === 100) {
                await screenshot(`${operationName}_${percent}`, `${operationName} at ${percent}%`);
              }
            }
            
            if (percent === 100) {
              console.log(`  ✅ ${operationName} complete!`);
              await page.waitForTimeout(2000); // Wait for UI to update
              return true;
            }
          }
        }
      } else {
        // Check if operation completed quickly
        await page.waitForTimeout(500);
        const successToast = await page.locator('.Toastify__toast--success').first();
        if (await successToast.isVisible()) {
          console.log(`  ✅ ${operationName} completed!`);
          return true;
        }
      }
      
      await page.waitForTimeout(300);
    }
    
    console.log(`  ⚠️ ${operationName} timed out`);
    return false;
  }

  try {
    console.log('\n⏳ Initializing services...');
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // ===========================================
    // STEP 1: CREATE TEST DATA
    // ===========================================
    console.log('\n📁 STEP 1: CREATING TEST DATA');
    console.log('='*50);
    
    const testDir = '/workspace/workflow_test_' + Date.now();
    fs.mkdirSync(testDir, { recursive: true });
    
    // Create a reasonable number of files for testing
    console.log('  Creating test files...');
    for (let i = 1; i <= 10; i++) {
      const content = `Test Document ${i}\n${'='.repeat(50)}\n` + 
                     `This is test content for file ${i}.\n` + 
                     'Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n'.repeat(50);
      fs.writeFileSync(path.join(testDir, `document_${i}.txt`), content);
    }
    
    console.log(`  ✅ Created 10 test files in ${testDir}`);
    workflowResults.steps.push({ step: 'CREATE_DATA', success: true, files: 10 });
    
    // ===========================================
    // STEP 2: ADD FOLDER
    // ===========================================
    console.log('\n➕ STEP 2: ADDING FOLDER');
    console.log('='*50);
    
    // Navigate to folders page
    await page.goto(`${FRONTEND_URL}/folders`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    await screenshot('initial', 'Initial folders page');
    
    // Add folder via API for reliability
    const addResponse = await fetch(`${API_URL}/add_folder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        path: testDir,
        name: 'Complete Workflow Test'
      })
    });
    
    const addData = await addResponse.json();
    const folderId = addData.folder_id;
    console.log(`  ✅ Folder added: ${folderId}`);
    workflowResults.steps.push({ step: 'ADD_FOLDER', success: true, folderId });
    
    // Reload and select folder
    await page.reload();
    await page.waitForTimeout(2000);
    
    // Click on the folder
    const folderSelector = 'text="Complete Workflow Test"';
    await page.waitForSelector(folderSelector, { timeout: 5000 });
    await page.click(folderSelector);
    await page.waitForTimeout(1000);
    await screenshot('folder_selected', 'Folder selected');
    
    // ===========================================
    // STEP 3: INDEX FILES
    // ===========================================
    console.log('\n🔍 STEP 3: INDEXING FILES');
    console.log('='*50);
    
    // Go to actions tab
    await page.click('button:text-is("actions")');
    await page.waitForTimeout(1000);
    
    // Click index button
    console.log('  Starting indexing...');
    await page.click('button:has-text("Index")');
    
    // Switch to overview to see progress
    await page.click('button:text-is("overview")');
    
    // Wait for indexing to complete
    const indexSuccess = await waitForOperation('Indexing', 30000);
    workflowResults.steps.push({ step: 'INDEX_FILES', success: indexSuccess });
    
    await page.waitForTimeout(2000);
    
    // ===========================================
    // STEP 4: SEGMENT FILES
    // ===========================================
    console.log('\n✂️ STEP 4: SEGMENTING FILES');
    console.log('='*50);
    
    // Go back to actions
    await page.click('button:text-is("actions")');
    await page.waitForTimeout(1000);
    
    // Click segment button
    console.log('  Starting segmentation...');
    const segmentButton = await page.locator('button:has-text("Segment")').first();
    
    if (await segmentButton.isEnabled()) {
      await segmentButton.click();
      
      // Switch to overview for progress
      await page.click('button:text-is("overview")');
      
      // Wait for segmentation
      const segmentSuccess = await waitForOperation('Segmenting', 30000);
      workflowResults.steps.push({ step: 'SEGMENT_FILES', success: segmentSuccess });
    } else {
      console.log('  ⚠️ Segment button disabled');
      workflowResults.steps.push({ step: 'SEGMENT_FILES', success: false, reason: 'Button disabled' });
    }
    
    await page.waitForTimeout(2000);
    
    // ===========================================
    // STEP 5: UPLOAD TO USENET
    // ===========================================
    console.log('\n📡 STEP 5: UPLOADING TO USENET');
    console.log('='*50);
    console.log('  Server: news.newshosting.com');
    console.log('  Username: contemptx');
    
    // Go to actions
    await page.click('button:text-is("actions")');
    await page.waitForTimeout(1000);
    
    // Try upload button
    const uploadButton = await page.locator('button:has-text("Upload")').first();
    
    if (await uploadButton.isEnabled()) {
      console.log('  Starting upload...');
      await uploadButton.click();
      
      // Switch to overview for progress
      await page.click('button:text-is("overview")');
      
      // Wait for upload
      const uploadSuccess = await waitForOperation('Uploading', 60000);
      workflowResults.steps.push({ step: 'UPLOAD_TO_USENET', success: uploadSuccess });
    } else {
      console.log('  ⚠️ Upload button disabled - attempting direct API call');
      
      // Try direct API upload
      const uploadResponse = await fetch(`${API_URL}/upload_folder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folderId })
      });
      
      const uploadData = await uploadResponse.json();
      console.log(`  API Response: ${uploadData.message || 'Upload initiated'}`);
      workflowResults.steps.push({ 
        step: 'UPLOAD_TO_USENET', 
        success: uploadData.success || false,
        method: 'API'
      });
    }
    
    await page.waitForTimeout(3000);
    
    // ===========================================
    // STEP 6: CREATE SHARES
    // ===========================================
    console.log('\n🔗 STEP 6: CREATING SHARES');
    console.log('='*50);
    
    // Navigate to overview first
    await page.click('button:text-is("overview")');
    await page.waitForTimeout(1000);
    
    // Look for Create Share button
    let shareCreated = false;
    const createShareBtn = await page.locator('button:has-text("Create Share")').first();
    
    if (await createShareBtn.isVisible()) {
      if (await createShareBtn.isEnabled()) {
        console.log('  Creating public share...');
        await createShareBtn.click();
        await page.waitForTimeout(1000);
        
        // Handle share dialog if it appears
        const shareTypeSelector = await page.locator('select, input[type="radio"]').first();
        if (await shareTypeSelector.isVisible()) {
          await screenshot('share_dialog', 'Share creation dialog');
          
          // Try to select public share
          const publicOption = await page.locator('label:has-text("Public")').first();
          if (await publicOption.isVisible()) {
            await publicOption.click();
          }
          
          // Click create/confirm
          const confirmBtn = await page.locator('button:has-text("Create"), button:has-text("Confirm")').last();
          if (await confirmBtn.isVisible()) {
            await confirmBtn.click();
            await page.waitForTimeout(2000);
            shareCreated = true;
          }
        }
      } else {
        console.log('  ⚠️ Create Share button disabled - trying API');
        
        // Try API share creation
        const shareResponse = await fetch(`${API_URL}/create_share`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            folderId,
            shareType: 'public',
            description: 'Test public share'
          })
        });
        
        if (shareResponse.ok) {
          const shareData = await shareResponse.json();
          console.log(`  ✅ Share created via API: ${shareData.shareId || 'unknown'}`);
          workflowResults.shareIds.push(shareData.shareId);
          shareCreated = true;
        }
      }
    }
    
    workflowResults.steps.push({ step: 'CREATE_SHARE', success: shareCreated });
    
    // Check shares tab
    const sharesTab = await page.locator('button:text-is("shares")').first();
    if (await sharesTab.isVisible()) {
      await sharesTab.click();
      await page.waitForTimeout(1000);
      await screenshot('shares_list', 'Shares list');
      
      // Look for share IDs
      const shareIdElements = await page.locator('code, .font-mono').all();
      for (const element of shareIdElements) {
        const text = await element.textContent();
        if (text && text.length > 10) {
          console.log(`  📋 Share ID found: ${text}`);
          workflowResults.shareIds.push(text);
        }
      }
    }
    
    // ===========================================
    // STEP 7: TEST DOWNLOAD
    // ===========================================
    console.log('\n⬇️ STEP 7: TESTING DOWNLOAD');
    console.log('='*50);
    
    if (workflowResults.shareIds.length > 0) {
      const shareId = workflowResults.shareIds[0];
      console.log(`  Testing download with share ID: ${shareId}`);
      
      // Navigate to download page if it exists
      const downloadLink = await page.locator('a:has-text("Download"), button:has-text("Download")').first();
      if (await downloadLink.isVisible()) {
        await downloadLink.click();
        await page.waitForTimeout(2000);
        await screenshot('download_page', 'Download interface');
        
        // Try to initiate download
        const downloadBtn = await page.locator('button:has-text("Start Download")').first();
        if (await downloadBtn.isVisible()) {
          await downloadBtn.click();
          console.log('  ✅ Download initiated');
          workflowResults.steps.push({ step: 'TEST_DOWNLOAD', success: true });
        }
      } else {
        console.log('  ℹ️ Download interface not available');
        workflowResults.steps.push({ step: 'TEST_DOWNLOAD', success: false, reason: 'No download UI' });
      }
    } else {
      console.log('  ⚠️ No share IDs available for download test');
      workflowResults.steps.push({ step: 'TEST_DOWNLOAD', success: false, reason: 'No share IDs' });
    }
    
    // Final screenshot
    await page.waitForTimeout(2000);
    await screenshot('final', 'Workflow complete');
    
    // ===========================================
    // GENERATE FINAL REPORT
    // ===========================================
    console.log('\n' + '='*70);
    console.log('📊 COMPLETE WORKFLOW RESULTS');
    console.log('='*70);
    
    console.log('\n✅ WORKFLOW STEPS:');
    workflowResults.steps.forEach((step, idx) => {
      const icon = step.success ? '✅' : '❌';
      console.log(`  ${idx + 1}. ${step.step}: ${icon}`);
      if (step.reason) console.log(`     Reason: ${step.reason}`);
      if (step.method) console.log(`     Method: ${step.method}`);
    });
    
    console.log('\n🔗 SHARE IDS GENERATED:');
    if (workflowResults.shareIds.length > 0) {
      workflowResults.shareIds.forEach(id => {
        console.log(`  • ${id}`);
      });
    } else {
      console.log('  No share IDs generated');
    }
    
    console.log('\n📸 SCREENSHOTS:');
    console.log(`  Total: ${screenshotCount} screenshots`);
    console.log(`  Location: ${OUTPUT_DIR}`);
    
    // Save report
    fs.writeFileSync(
      `${OUTPUT_DIR}/workflow_report.json`,
      JSON.stringify(workflowResults, null, 2)
    );
    
    console.log('\n📄 DETAILED REPORT:');
    console.log(`  ${OUTPUT_DIR}/workflow_report.json`);
    
  } catch (error) {
    console.error('\n❌ Workflow error:', error.message);
    await screenshot('error', error.message);
  } finally {
    await page.waitForTimeout(5000);
    await context.close();
    await browser.close();
    
    // Wait for video
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Rename video
    const files = fs.readdirSync(VIDEO_DIR);
    const videoFile = files.find(f => f.endsWith('.webm'));
    
    if (videoFile) {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const newName = `complete_workflow_${timestamp}.webm`;
      fs.renameSync(
        path.join(VIDEO_DIR, videoFile),
        path.join(VIDEO_DIR, newName)
      );
      
      console.log('\n🎥 VIDEO RECORDING:');
      console.log(`  ${VIDEO_DIR}/${newName}`);
      console.log(`  Size: ${(fs.statSync(path.join(VIDEO_DIR, newName)).size / 1024 / 1024).toFixed(2)} MB`);
    }
    
    console.log('\n✅ WORKFLOW COMPLETE!');
  }
}

// Execute the complete workflow
completeFolderWorkflow().catch(console.error);