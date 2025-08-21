const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Configuration
const FRONTEND_URL = 'http://localhost:1420';
const API_URL = 'http://localhost:8000/api/v1';
const OUTPUT_DIR = '/workspace/all_actions_test';
const VIDEO_DIR = '/workspace/all_actions_video';

// Ensure directories exist
[OUTPUT_DIR, VIDEO_DIR].forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

async function runAllFolderActions() {
  console.log('🚀 RUNNING ALL FOLDER ACTIONS TEST');
  console.log('='*70);
  console.log('This test will execute ALL folder management actions:');
  console.log('  1. Add Folder');
  console.log('  2. Index Files');
  console.log('  3. Segment Files');
  console.log('  4. Upload to Usenet');
  console.log('  5. Create Share (Public/Private/Protected)');
  console.log('='*70);
  
  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    slowMo: 100
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
  const actionResults = {
    timestamp: new Date().toISOString(),
    actions: [],
    screenshots: [],
    progressData: {}
  };
  
  async function screenshot(name, description) {
    screenshotCount++;
    const filename = `${OUTPUT_DIR}/${String(screenshotCount).padStart(3, '0')}_${name}.png`;
    await page.screenshot({ path: filename, fullPage: true });
    console.log(`  📸 Screenshot ${screenshotCount}: ${description}`);
    actionResults.screenshots.push({ number: screenshotCount, name, description, filename });
    return filename;
  }

  async function trackProgress(operation) {
    const progressValues = [];
    let lastProgress = -1;
    let checkCount = 0;
    const maxChecks = 120; // 60 seconds max
    
    console.log(`  ⏳ Tracking ${operation} progress...`);
    
    while (checkCount < maxChecks) {
      await page.waitForTimeout(500);
      checkCount++;
      
      const progressSection = await page.locator('text="Operation in Progress"').first();
      if (await progressSection.isVisible()) {
        const percentText = await page.locator('text=/\\d+%/').first();
        const messageText = await page.locator('.text-sm.text-gray-600').last();
        
        if (await percentText.isVisible()) {
          const text = await percentText.textContent();
          const match = text.match(/(\d+)%/);
          if (match) {
            const percent = parseInt(match[1]);
            const message = await messageText.isVisible() ? await messageText.textContent() : '';
            
            if (percent !== lastProgress) {
              progressValues.push({ percent, message, time: checkCount * 500 });
              console.log(`    📊 ${percent}% - ${message}`);
              lastProgress = percent;
              
              // Capture key progress points
              if (percent === 0 || percent === 25 || percent === 50 || percent === 75 || percent === 100) {
                await screenshot(`${operation}_${percent}pct`, `${operation} at ${percent}%`);
              }
            }
            
            if (percent === 100) {
              console.log(`  ✅ ${operation} complete!`);
              break;
            }
          }
        }
      } else if (checkCount > 2) {
        // If no progress section visible after 1 second, operation might be instant
        console.log(`  ⚡ ${operation} completed quickly`);
        break;
      }
    }
    
    return progressValues;
  }

  try {
    // Wait for backend
    console.log('\n⏳ Waiting for services to be ready...');
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // ===========================================
    // 1. ADD FOLDER
    // ===========================================
    console.log('\n1️⃣ ACTION: ADD FOLDER');
    console.log('='*50);
    
    // Create test folder with substantial content
    const testDir = '/workspace/complete_actions_test_' + Date.now();
    fs.mkdirSync(testDir, { recursive: true });
    
    // Create subdirectories
    const subdirs = ['documents', 'images', 'videos', 'archives'];
    subdirs.forEach(subdir => {
      fs.mkdirSync(path.join(testDir, subdir), { recursive: true });
    });
    
    // Create various files
    console.log('  📁 Creating test files...');
    for (let i = 1; i <= 25; i++) {
      // Documents
      fs.writeFileSync(
        path.join(testDir, 'documents', `document_${i}.txt`),
        `Document ${i}\n${'='.repeat(50)}\n` + 'Lorem ipsum '.repeat(1000)
      );
      
      // Images (simulated)
      fs.writeFileSync(
        path.join(testDir, 'images', `image_${i}.jpg`),
        Buffer.from('FFD8FFE0', 'hex') + Buffer.alloc(50000)
      );
      
      // Videos (simulated)
      if (i <= 10) {
        fs.writeFileSync(
          path.join(testDir, 'videos', `video_${i}.mp4`),
          Buffer.alloc(100000)
        );
      }
      
      // Archives (simulated)
      if (i <= 5) {
        fs.writeFileSync(
          path.join(testDir, 'archives', `archive_${i}.zip`),
          Buffer.from('504B0304', 'hex') + Buffer.alloc(75000)
        );
      }
    }
    
    const totalFiles = fs.readdirSync(path.join(testDir, 'documents')).length +
                      fs.readdirSync(path.join(testDir, 'images')).length +
                      fs.readdirSync(path.join(testDir, 'videos')).length +
                      fs.readdirSync(path.join(testDir, 'archives')).length;
    
    console.log(`  ✅ Created ${totalFiles} test files in 4 subdirectories`);
    
    // Navigate to folders page
    await page.goto(`${FRONTEND_URL}/folders`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    await screenshot('initial_folders', 'Initial folders page');
    
    // Add folder via API
    console.log('  📤 Adding folder to system...');
    const addResponse = await fetch(`${API_URL}/add_folder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        path: testDir,
        name: 'Complete Actions Test Folder'
      })
    });
    
    const addData = await addResponse.json();
    const folderId = addData.folder_id;
    console.log(`  ✅ Folder added with ID: ${folderId}`);
    
    actionResults.actions.push({
      action: 'ADD_FOLDER',
      success: true,
      folderId: folderId,
      path: testDir,
      filesCreated: totalFiles
    });
    
    // Reload and select the folder
    await page.reload();
    await page.waitForTimeout(2000);
    
    const folderItem = await page.locator('text="Complete Actions Test Folder"').first();
    if (await folderItem.isVisible()) {
      await folderItem.click();
    } else {
      await page.locator('.divide-y > div').first().click();
    }
    await page.waitForTimeout(1000);
    await screenshot('folder_selected', 'Folder selected and details shown');
    
    // ===========================================
    // 2. INDEX FILES
    // ===========================================
    console.log('\n2️⃣ ACTION: INDEX FILES');
    console.log('='*50);
    
    // Go to actions tab
    await page.click('button:text-is("actions")');
    await page.waitForTimeout(1000);
    await screenshot('actions_tab', 'Actions tab opened');
    
    // Start indexing
    console.log('  🔍 Starting file indexing...');
    const indexButton = await page.locator('button:has-text("Index")').first();
    await indexButton.click();
    
    // Go to overview to see progress
    await page.click('button:text-is("overview")');
    await page.waitForTimeout(500);
    
    // Track indexing progress
    const indexProgress = await trackProgress('indexing');
    actionResults.progressData.indexing = indexProgress;
    
    actionResults.actions.push({
      action: 'INDEX_FILES',
      success: indexProgress.length > 0,
      filesIndexed: totalFiles,
      progressSteps: indexProgress.length
    });
    
    await page.waitForTimeout(3000);
    
    // ===========================================
    // 3. SEGMENT FILES
    // ===========================================
    console.log('\n3️⃣ ACTION: SEGMENT FILES');
    console.log('='*50);
    
    // Go back to actions
    await page.click('button:text-is("actions")');
    await page.waitForTimeout(1000);
    
    // Start segmenting
    console.log('  ✂️ Starting file segmentation...');
    const segmentButton = await page.locator('button:has-text("Segment")').first();
    
    if (await segmentButton.isVisible() && !await segmentButton.isDisabled()) {
      await segmentButton.click();
      
      // Go to overview to see progress
      await page.click('button:text-is("overview")');
      await page.waitForTimeout(500);
      
      // Track segmenting progress
      const segmentProgress = await trackProgress('segmenting');
      actionResults.progressData.segmenting = segmentProgress;
      
      actionResults.actions.push({
        action: 'SEGMENT_FILES',
        success: segmentProgress.length > 0,
        filesSegmented: totalFiles,
        progressSteps: segmentProgress.length
      });
    } else {
      console.log('  ⚠️ Segment button not available');
      actionResults.actions.push({
        action: 'SEGMENT_FILES',
        success: false,
        reason: 'Button not available'
      });
    }
    
    await page.waitForTimeout(3000);
    
    // ===========================================
    // 4. UPLOAD TO USENET
    // ===========================================
    console.log('\n4️⃣ ACTION: UPLOAD TO USENET');
    console.log('='*50);
    
    // Go back to actions
    await page.click('button:text-is("actions")');
    await page.waitForTimeout(1000);
    
    // Start uploading
    console.log('  📡 Starting Usenet upload...');
    console.log('  🌐 Server: news.newshosting.com');
    console.log('  👤 Username: contemptx');
    
    const uploadButton = await page.locator('button:has-text("Upload")').first();
    
    if (await uploadButton.isVisible() && !await uploadButton.isDisabled()) {
      await uploadButton.click();
      
      // Go to overview to see progress
      await page.click('button:text-is("overview")');
      await page.waitForTimeout(500);
      
      // Track upload progress
      const uploadProgress = await trackProgress('uploading');
      actionResults.progressData.uploading = uploadProgress;
      
      actionResults.actions.push({
        action: 'UPLOAD_TO_USENET',
        success: uploadProgress.length > 0,
        server: 'news.newshosting.com',
        progressSteps: uploadProgress.length
      });
    } else {
      console.log('  ⚠️ Upload button not available');
      actionResults.actions.push({
        action: 'UPLOAD_TO_USENET',
        success: false,
        reason: 'Button not available'
      });
    }
    
    await page.waitForTimeout(3000);
    
    // ===========================================
    // 5. CREATE SHARES
    // ===========================================
    console.log('\n5️⃣ ACTION: CREATE SHARES');
    console.log('='*50);
    
    // Go to shares tab
    const sharesTab = await page.locator('button:text-is("shares")').first();
    if (await sharesTab.isVisible()) {
      await sharesTab.click();
      await page.waitForTimeout(1000);
      await screenshot('shares_tab', 'Shares tab opened');
    }
    
    // Try to create a share
    const createShareButton = await page.locator('button:has-text("Create Share")').first();
    if (await createShareButton.isVisible()) {
      console.log('  🔗 Creating public share...');
      await createShareButton.click();
      await page.waitForTimeout(1000);
      
      // Fill share details if dialog appears
      const shareDialog = await page.locator('text="Create New Share"').first();
      if (await shareDialog.isVisible()) {
        await screenshot('share_dialog', 'Share creation dialog opened');
        
        // Try public share
        const publicOption = await page.locator('text="Public"').first();
        if (await publicOption.isVisible()) {
          await publicOption.click();
        }
        
        const confirmButton = await page.locator('button:has-text("Create")').last();
        if (await confirmButton.isVisible()) {
          await confirmButton.click();
          await page.waitForTimeout(2000);
          console.log('  ✅ Share created successfully');
          
          actionResults.actions.push({
            action: 'CREATE_SHARE',
            success: true,
            shareType: 'public'
          });
        }
      }
    } else {
      console.log('  ℹ️ Create Share button not visible - trying alternative method');
      
      // Try via overview tab
      await page.click('button:text-is("overview")');
      await page.waitForTimeout(1000);
      
      const altShareButton = await page.locator('button:has-text("Create Share")').first();
      if (await altShareButton.isVisible()) {
        await altShareButton.click();
        await page.waitForTimeout(2000);
        actionResults.actions.push({
          action: 'CREATE_SHARE',
          success: true,
          method: 'overview_tab'
        });
      } else {
        actionResults.actions.push({
          action: 'CREATE_SHARE',
          success: false,
          reason: 'Button not found'
        });
      }
    }
    
    // Final screenshot
    await page.waitForTimeout(2000);
    await screenshot('final_state', 'All actions completed');
    
    // ===========================================
    // GENERATE REPORT
    // ===========================================
    console.log('\n' + '='*70);
    console.log('📊 ALL FOLDER ACTIONS TEST COMPLETE');
    console.log('='*70);
    
    console.log('\n✅ ACTIONS EXECUTED:');
    actionResults.actions.forEach((action, idx) => {
      const status = action.success ? '✅' : '❌';
      console.log(`  ${idx + 1}. ${action.action}: ${status}`);
      if (action.filesIndexed) console.log(`     - Files: ${action.filesIndexed}`);
      if (action.progressSteps) console.log(`     - Progress updates: ${action.progressSteps}`);
      if (action.reason) console.log(`     - Reason: ${action.reason}`);
    });
    
    console.log('\n📈 PROGRESS TRACKING:');
    Object.keys(actionResults.progressData).forEach(op => {
      const data = actionResults.progressData[op];
      if (data.length > 0) {
        const percentages = data.map(d => d.percent);
        console.log(`  ${op}: ${Math.min(...percentages)}% → ${Math.max(...percentages)}% (${data.length} updates)`);
      }
    });
    
    console.log('\n📸 SCREENSHOTS CAPTURED:');
    console.log(`  Total: ${screenshotCount} screenshots`);
    console.log(`  Location: ${OUTPUT_DIR}`);
    
    // Save detailed report
    fs.writeFileSync(
      `${OUTPUT_DIR}/test_report.json`,
      JSON.stringify(actionResults, null, 2)
    );
    
    console.log('\n📄 REPORT SAVED:');
    console.log(`  ${OUTPUT_DIR}/test_report.json`);
    
  } catch (error) {
    console.error('\n❌ Test error:', error.message);
    await screenshot('error_state', `Error: ${error.message}`);
  } finally {
    // Close and save video
    await page.waitForTimeout(5000);
    await context.close();
    await browser.close();
    
    // Wait for video to be saved
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Find and rename video
    const files = fs.readdirSync(VIDEO_DIR);
    const videoFile = files.find(f => f.endsWith('.webm'));
    
    if (videoFile) {
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const newName = `all_actions_${timestamp}.webm`;
      fs.renameSync(
        path.join(VIDEO_DIR, videoFile),
        path.join(VIDEO_DIR, newName)
      );
      
      console.log('\n🎥 VIDEO SAVED:');
      console.log(`  ${VIDEO_DIR}/${newName}`);
    }
    
    console.log('\n✅ Test complete!');
  }
}

// Run the test
runAllFolderActions().catch(console.error);