const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Configuration
const FRONTEND_URL = 'http://localhost:1420';
const API_URL = 'http://localhost:8000/api/v1';
const SCREENSHOT_DIR = '/workspace/real_progress_screenshots';

// Ensure screenshot directory exists
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function testRealProgress() {
  console.log('🚀 TESTING REAL PROGRESS INDICATORS');
  console.log('='*60);
  
  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    slowMo: 100 // Slow down to see progress
  });

  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 }
  });

  let screenshotCount = 0;
  async function screenshot(name) {
    screenshotCount++;
    const filename = `${SCREENSHOT_DIR}/${String(screenshotCount).padStart(2, '0')}_${name}.png`;
    await page.screenshot({ path: filename, fullPage: true });
    console.log(`📸 Screenshot ${screenshotCount}: ${name}`);
    return filename;
  }

  try {
    // Navigate to folders page
    console.log('\n1️⃣ NAVIGATING TO FOLDERS');
    await page.goto(`${FRONTEND_URL}/folders`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
    await screenshot('initial_folders_page');
    
    // Check if backend is responding
    console.log('\n2️⃣ CHECKING BACKEND STATUS');
    const testResponse = await fetch(`${API_URL}/folders`);
    console.log(`  Backend status: ${testResponse.status}`);
    
    // Create a test folder with real files
    console.log('\n3️⃣ CREATING TEST FOLDER');
    const testDir = '/workspace/real_test_' + Date.now();
    fs.mkdirSync(testDir, { recursive: true });
    
    // Create test files
    for (let i = 1; i <= 3; i++) {
      const content = `Test file ${i}\n` + 'x'.repeat(10000);
      fs.writeFileSync(path.join(testDir, `file${i}.txt`), content);
    }
    console.log(`  Created test folder: ${testDir}`);
    
    // Add folder via API
    const addResponse = await fetch(`${API_URL}/add_folder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        path: testDir,
        name: 'Real Progress Test'
      })
    });
    
    const addData = await addResponse.json();
    const folderId = addData.folder_id;
    console.log(`  Folder added with ID: ${folderId}`);
    
    // Reload page to see new folder
    await page.reload();
    await page.waitForTimeout(1500);
    await screenshot('folder_added');
    
    // Click on the folder
    console.log('\n4️⃣ SELECTING FOLDER');
    const folderItem = await page.locator('.divide-y > div').first();
    await folderItem.click();
    await page.waitForTimeout(1000);
    await screenshot('folder_selected');
    
    // Go to actions tab
    console.log('\n5️⃣ TESTING INDEXING');
    await page.click('button:text-is("actions")');
    await page.waitForTimeout(500);
    await screenshot('actions_tab');
    
    // Monitor network for API calls
    let indexingStarted = false;
    page.on('response', response => {
      if (response.url().includes('index_folder')) {
        console.log(`  📡 Index API called: ${response.status()}`);
        if (!indexingStarted) {
          indexingStarted = true;
          screenshot('indexing_api_called').catch(() => {});
        }
      }
    });
    
    // Click index button
    const indexButton = await page.locator('button:has-text("Index")').first();
    if (await indexButton.isVisible()) {
      console.log('  Clicking Index button...');
      await indexButton.click();
      
      // Try to capture any progress indicators
      for (let i = 1; i <= 5; i++) {
        await page.waitForTimeout(500);
        
        // Look for any loading indicators
        const spinners = await page.locator('.animate-spin, .animate-pulse').count();
        const progressBars = await page.locator('[role="progressbar"], .progress, .bg-blue-600').count();
        const loadingTexts = await page.locator('text=/loading|indexing|processing/i').count();
        
        console.log(`  Check ${i}: Spinners=${spinners}, Progress=${progressBars}, Loading=${loadingTexts}`);
        
        if (spinners > 0 || progressBars > 0 || loadingTexts > 0) {
          await screenshot(`indexing_progress_${i}`);
          console.log(`  ✅ Progress indicator found!`);
        } else {
          await screenshot(`indexing_state_${i}`);
        }
      }
    }
    
    // Check files tab
    await page.click('button:text-is("files")');
    await page.waitForTimeout(1000);
    await screenshot('files_after_index');
    
    // Test segmenting
    console.log('\n6️⃣ TESTING SEGMENTING');
    await page.click('button:text-is("actions")');
    await page.waitForTimeout(500);
    
    const segmentButton = await page.locator('button:has-text("Segment")').first();
    if (await segmentButton.isVisible() && !await segmentButton.isDisabled()) {
      console.log('  Clicking Segment button...');
      await segmentButton.click();
      
      // Capture progress
      for (let i = 1; i <= 3; i++) {
        await page.waitForTimeout(500);
        await screenshot(`segmenting_state_${i}`);
      }
    }
    
    // Final state
    console.log('\n7️⃣ FINAL STATE');
    await page.click('button:text-is("overview")');
    await page.waitForTimeout(1000);
    await screenshot('final_overview');
    
    // Check console for errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    if (consoleErrors.length > 0) {
      console.log('\n⚠️ Console errors detected:');
      consoleErrors.forEach(err => console.log(`  - ${err}`));
    }
    
    console.log('\n' + '='*60);
    console.log('📊 TEST SUMMARY');
    console.log('='*60);
    console.log(`  Screenshots taken: ${screenshotCount}`);
    console.log(`  Location: ${SCREENSHOT_DIR}`);
    console.log(`  Backend responding: ${testResponse.ok ? 'Yes' : 'No'}`);
    console.log(`  Folder created: ${folderId ? 'Yes' : 'No'}`);
    console.log(`  Progress indicators found: ${indexingStarted ? 'Maybe' : 'No'}`);
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
    await screenshot('error_state');
  } finally {
    await page.waitForTimeout(2000);
    await browser.close();
    console.log('\n✅ Test complete');
  }
}

// Run the test
testRealProgress().catch(console.error);