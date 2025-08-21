const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Configuration
const FRONTEND_URL = 'http://localhost:1420';
const API_URL = 'http://localhost:8000/api/v1';
const SCREENSHOT_DIR = '/workspace/real_progress_test';

// Ensure screenshot directory exists
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function testRealProgressBars() {
  console.log('🎯 TESTING REAL PROGRESS BARS');
  console.log('='*70);
  
  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    slowMo: 50
  });

  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 }
  });

  let screenshotCount = 0;
  async function screenshot(name) {
    screenshotCount++;
    const filename = `${SCREENSHOT_DIR}/${String(screenshotCount).padStart(2, '0')}_${name}.png`;
    await page.screenshot({ path: filename, fullPage: true });
    console.log(`  📸 Screenshot ${screenshotCount}: ${name}`);
    return filename;
  }

  try {
    // Wait for backend
    console.log('\n1️⃣ CHECKING BACKEND');
    await new Promise(resolve => setTimeout(resolve, 3000));
    const backendCheck = await fetch(`${API_URL}/folders`);
    console.log(`  Backend status: ${backendCheck.status}`);
    
    // Navigate to folders
    console.log('\n2️⃣ NAVIGATING TO FOLDERS');
    await page.goto(`${FRONTEND_URL}/folders`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    await screenshot('initial_page');
    
    // Create test folder with multiple files
    console.log('\n3️⃣ CREATING TEST FOLDER WITH MULTIPLE FILES');
    const testDir = '/workspace/progress_bar_test_' + Date.now();
    fs.mkdirSync(testDir, { recursive: true });
    
    // Create 10 test files
    for (let i = 1; i <= 10; i++) {
      const content = `Test file ${i}\n` + 'x'.repeat(5000 * i);
      fs.writeFileSync(path.join(testDir, `file${i}.txt`), content);
    }
    console.log(`  Created 10 test files in ${testDir}`);
    
    // Add folder via API
    const addResponse = await fetch(`${API_URL}/add_folder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        path: testDir,
        name: 'Progress Bar Test'
      })
    });
    
    const addData = await addResponse.json();
    const folderId = addData.folder_id;
    console.log(`  Folder added: ${folderId}`);
    
    // Reload page
    await page.reload();
    await page.waitForTimeout(2000);
    
    // Select the folder
    console.log('\n4️⃣ SELECTING FOLDER');
    const folderItem = await page.locator('.divide-y > div').first();
    await folderItem.click();
    await page.waitForTimeout(1000);
    await screenshot('folder_selected');
    
    // Go to actions tab
    console.log('\n5️⃣ STARTING INDEXING OPERATION');
    await page.click('button:text-is("actions")');
    await page.waitForTimeout(1000);
    await screenshot('actions_tab');
    
    // Click index button
    const indexButton = await page.locator('button:has-text("Index")').first();
    if (await indexButton.isVisible()) {
      console.log('  Clicking Index button...');
      await indexButton.click();
      
      // Now look for the progress bar
      console.log('\n6️⃣ MONITORING PROGRESS BAR');
      
      // Go back to overview tab to see progress
      await page.click('button:text-is("overview")');
      await page.waitForTimeout(500);
      
      let progressFound = false;
      let progressValues = [];
      
      // Monitor for up to 30 seconds
      for (let i = 0; i < 60; i++) {
        await page.waitForTimeout(500);
        
        // Look for progress bar elements
        const progressBar = await page.locator('[role="progressbar"], .bg-blue-600, [style*="width"]').first();
        const progressText = await page.locator('text=/\d+%/').first();
        const messageText = await page.locator('text=/Indexing.*file/i').first();
        
        // Check if "Operation in Progress" section exists
        const operationSection = await page.locator('text="Operation in Progress"').first();
        
        if (await operationSection.isVisible()) {
          console.log('  ✅ Progress section found!');
          progressFound = true;
          
          // Capture the progress value
          if (await progressText.isVisible()) {
            const text = await progressText.textContent();
            const match = text.match(/(\d+)%/);
            if (match) {
              const value = parseInt(match[1]);
              progressValues.push(value);
              console.log(`  📊 Progress: ${value}%`);
              
              // Take screenshots at key progress points
              if (value === 0 || value === 25 || value === 50 || value === 75 || value === 100) {
                await screenshot(`progress_${value}_percent`);
              } else if (i % 5 === 0) {
                await screenshot(`progress_state_${i}`);
              }
            }
          }
          
          // Check for message
          if (await messageText.isVisible()) {
            const message = await messageText.textContent();
            console.log(`  📝 Message: ${message}`);
          }
          
          // Check if completed
          if (progressValues.length > 0 && progressValues[progressValues.length - 1] === 100) {
            console.log('  ✅ Indexing completed!');
            await screenshot('indexing_complete');
            break;
          }
        } else if (i % 10 === 0) {
          console.log(`  ⏳ Waiting for progress bar... (${i/2}s)`);
          await screenshot(`waiting_${i}`);
        }
      }
      
      // Analyze results
      console.log('\n7️⃣ ANALYSIS');
      if (progressFound) {
        console.log('  ✅ REAL PROGRESS BAR DETECTED!');
        console.log(`  Progress values captured: ${progressValues.join(', ')}`);
        
        // Check if progress actually increased
        let isIncreasing = true;
        for (let i = 1; i < progressValues.length; i++) {
          if (progressValues[i] < progressValues[i-1]) {
            isIncreasing = false;
            break;
          }
        }
        
        if (isIncreasing && progressValues.length > 1) {
          console.log('  ✅ Progress bar shows real incremental progress!');
        } else {
          console.log('  ⚠️ Progress values did not increase properly');
        }
      } else {
        console.log('  ❌ No progress bar found');
      }
      
      // Final screenshot
      await page.waitForTimeout(2000);
      await screenshot('final_state');
    }
    
    console.log('\n' + '='*70);
    console.log('📊 TEST SUMMARY');
    console.log('='*70);
    console.log(`  Screenshots taken: ${screenshotCount}`);
    console.log(`  Progress bar found: ${progressFound ? 'YES' : 'NO'}`);
    console.log(`  Progress values: ${progressValues.length > 0 ? progressValues.join(', ') : 'None'}`);
    console.log(`  Location: ${SCREENSHOT_DIR}`);
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
    await screenshot('error_state');
  } finally {
    await page.waitForTimeout(3000);
    await browser.close();
    console.log('\n✅ Test complete');
  }
}

// Run the test
testRealProgressBars().catch(console.error);