const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Configuration
const FRONTEND_URL = 'http://localhost:1420';
const API_URL = 'http://localhost:8000/api/v1';
const SCREENSHOT_DIR = '/workspace/complete_progress_test';

// Ensure screenshot directory exists
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function testAllProgressIndicators() {
  console.log('🎯 TESTING ALL PROGRESS INDICATORS');
  console.log('='*70);
  console.log('This test will demonstrate:');
  console.log('  1. Indexing progress (0% → 100%)');
  console.log('  2. Segmenting progress (0% → 100%)');
  console.log('  3. Uploading progress (0% → 100%)');
  console.log('='*70);
  
  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    slowMo: 100
  });

  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 }
  });

  let screenshotCount = 0;
  const screenshots = [];
  
  async function screenshot(name, description) {
    screenshotCount++;
    const filename = `${SCREENSHOT_DIR}/${String(screenshotCount).padStart(3, '0')}_${name}.png`;
    await page.screenshot({ path: filename, fullPage: true });
    console.log(`  📸 ${screenshotCount}: ${description || name}`);
    screenshots.push({ number: screenshotCount, name, description, filename });
    return filename;
  }

  try {
    // Wait for backend
    console.log('\n⏳ Waiting for backend to be ready...');
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // Navigate to folders
    console.log('\n1️⃣ SETUP');
    await page.goto(`${FRONTEND_URL}/folders`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    await screenshot('initial_state', 'Initial folders page');
    
    // Create test folder with files
    console.log('\n2️⃣ CREATING TEST DATA');
    const testDir = '/workspace/complete_test_' + Date.now();
    fs.mkdirSync(testDir, { recursive: true });
    
    // Create 20 test files for better progress visualization
    for (let i = 1; i <= 20; i++) {
      const content = `Test file ${i}\n` + 'x'.repeat(1000 * i);
      fs.writeFileSync(path.join(testDir, `document_${i}.txt`), content);
    }
    console.log(`  Created 20 test files in ${testDir}`);
    
    // Add folder via API
    const addResponse = await fetch(`${API_URL}/add_folder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        path: testDir,
        name: 'Complete Progress Test'
      })
    });
    
    const addData = await addResponse.json();
    const folderId = addData.folder_id;
    console.log(`  Folder added: ${folderId}`);
    
    // Reload and select folder
    await page.reload();
    await page.waitForTimeout(2000);
    const folderItem = await page.locator('.divide-y > div').first();
    await folderItem.click();
    await page.waitForTimeout(1000);
    await screenshot('folder_selected', 'Test folder selected');
    
    // ===========================================
    // TEST INDEXING PROGRESS
    // ===========================================
    console.log('\n3️⃣ TESTING INDEXING PROGRESS');
    
    // Go to actions tab
    await page.click('button:text-is("actions")');
    await page.waitForTimeout(1000);
    await screenshot('actions_tab', 'Actions tab opened');
    
    // Click index button
    const indexButton = await page.locator('button:has-text("Index")').first();
    await indexButton.click();
    console.log('  Started indexing...');
    
    // Go to overview to see progress
    await page.click('button:text-is("overview")');
    await page.waitForTimeout(500);
    
    // Monitor indexing progress
    let indexProgress = [];
    for (let i = 0; i < 20; i++) {
      await page.waitForTimeout(300);
      
      const progressSection = await page.locator('text="Operation in Progress"').first();
      if (await progressSection.isVisible()) {
        const percentText = await page.locator('text=/\\d+%/').first();
        if (await percentText.isVisible()) {
          const text = await percentText.textContent();
          const match = text.match(/(\d+)%/);
          if (match) {
            const percent = parseInt(match[1]);
            indexProgress.push(percent);
            console.log(`  📊 Indexing: ${percent}%`);
            
            if (percent === 0 || percent === 25 || percent === 50 || percent === 75 || percent === 100) {
              await screenshot(`indexing_${percent}`, `Indexing at ${percent}%`);
            }
            
            if (percent === 100) break;
          }
        }
      }
    }
    
    await page.waitForTimeout(3000);
    console.log(`  ✅ Indexing complete: ${indexProgress.join(', ')}%`);
    
    // ===========================================
    // TEST SEGMENTING PROGRESS
    // ===========================================
    console.log('\n4️⃣ TESTING SEGMENTING PROGRESS');
    
    // Go back to actions
    await page.click('button:text-is("actions")');
    await page.waitForTimeout(1000);
    
    // Click segment button
    const segmentButton = await page.locator('button:has-text("Segment")').first();
    if (await segmentButton.isVisible() && !await segmentButton.isDisabled()) {
      await segmentButton.click();
      console.log('  Started segmenting...');
      
      // Go to overview to see progress
      await page.click('button:text-is("overview")');
      await page.waitForTimeout(500);
      
      // Monitor segmenting progress
      let segmentProgress = [];
      for (let i = 0; i < 20; i++) {
        await page.waitForTimeout(300);
        
        const progressSection = await page.locator('text="Operation in Progress"').first();
        if (await progressSection.isVisible()) {
          const percentText = await page.locator('text=/\\d+%/').first();
          if (await percentText.isVisible()) {
            const text = await percentText.textContent();
            const match = text.match(/(\d+)%/);
            if (match) {
              const percent = parseInt(match[1]);
              segmentProgress.push(percent);
              console.log(`  📊 Segmenting: ${percent}%`);
              
              if (percent === 0 || percent === 25 || percent === 50 || percent === 75 || percent === 100) {
                await screenshot(`segmenting_${percent}`, `Segmenting at ${percent}%`);
              }
              
              if (percent === 100) break;
            }
          }
        }
      }
      
      await page.waitForTimeout(3000);
      console.log(`  ✅ Segmenting complete: ${segmentProgress.join(', ')}%`);
    }
    
    // ===========================================
    // TEST UPLOADING PROGRESS
    // ===========================================
    console.log('\n5️⃣ TESTING UPLOADING PROGRESS');
    
    // Go back to actions
    await page.click('button:text-is("actions")');
    await page.waitForTimeout(1000);
    
    // Click upload button
    const uploadButton = await page.locator('button:has-text("Upload")').first();
    if (await uploadButton.isVisible() && !await uploadButton.isDisabled()) {
      await uploadButton.click();
      console.log('  Started uploading to Usenet...');
      console.log('  Server: news.newshosting.com');
      console.log('  Username: contemptx');
      
      // Go to overview to see progress
      await page.click('button:text-is("overview")');
      await page.waitForTimeout(500);
      
      // Monitor uploading progress
      let uploadProgress = [];
      for (let i = 0; i < 30; i++) {
        await page.waitForTimeout(300);
        
        const progressSection = await page.locator('text="Operation in Progress"').first();
        if (await progressSection.isVisible()) {
          const percentText = await page.locator('text=/\\d+%/').first();
          const messageText = await page.locator('text=/Uploading.*segment/i').first();
          
          if (await percentText.isVisible()) {
            const text = await percentText.textContent();
            const match = text.match(/(\d+)%/);
            if (match) {
              const percent = parseInt(match[1]);
              uploadProgress.push(percent);
              
              if (await messageText.isVisible()) {
                const msg = await messageText.textContent();
                console.log(`  📊 Uploading: ${percent}% - ${msg}`);
              } else {
                console.log(`  📊 Uploading: ${percent}%`);
              }
              
              if (percent === 0 || percent === 25 || percent === 50 || percent === 75 || percent === 100) {
                await screenshot(`uploading_${percent}`, `Uploading at ${percent}%`);
              }
              
              if (percent === 100) break;
            }
          }
        }
      }
      
      await page.waitForTimeout(3000);
      console.log(`  ✅ Uploading complete: ${uploadProgress.join(', ')}%`);
    }
    
    // Final screenshot
    await screenshot('final_state', 'All operations completed');
    
    // ===========================================
    // GENERATE REPORT
    // ===========================================
    console.log('\n' + '='*70);
    console.log('📊 COMPREHENSIVE TEST REPORT');
    console.log('='*70);
    
    console.log('\n📸 SCREENSHOTS CAPTURED:');
    screenshots.forEach(s => {
      console.log(`  ${s.number}. ${s.description}`);
    });
    
    console.log('\n✅ PROGRESS TRACKING RESULTS:');
    console.log(`  Indexing:   ${indexProgress.length > 0 ? '✅ Working' : '❌ Not found'} - Values: ${indexProgress.join(', ')}%`);
    console.log(`  Segmenting: ${segmentProgress.length > 0 ? '✅ Working' : '❌ Not found'} - Values: ${segmentProgress.join(', ')}%`);
    console.log(`  Uploading:  ${uploadProgress.length > 0 ? '✅ Working' : '❌ Not found'} - Values: ${uploadProgress.join(', ')}%`);
    
    console.log('\n📁 ARTIFACTS:');
    console.log(`  Screenshots: ${SCREENSHOT_DIR}`);
    console.log(`  Total: ${screenshotCount} screenshots`);
    
    // Save detailed report
    const report = {
      timestamp: new Date().toISOString(),
      test: 'Complete Progress Indicators Test',
      results: {
        indexing: {
          working: indexProgress.length > 0,
          values: indexProgress,
          screenshots: screenshots.filter(s => s.name.includes('indexing'))
        },
        segmenting: {
          working: segmentProgress.length > 0,
          values: segmentProgress,
          screenshots: screenshots.filter(s => s.name.includes('segmenting'))
        },
        uploading: {
          working: uploadProgress.length > 0,
          values: uploadProgress,
          screenshots: screenshots.filter(s => s.name.includes('uploading'))
        }
      },
      total_screenshots: screenshotCount,
      folder_id: folderId,
      test_directory: testDir
    };
    
    fs.writeFileSync(`${SCREENSHOT_DIR}/test_report.json`, JSON.stringify(report, null, 2));
    console.log(`  Report: ${SCREENSHOT_DIR}/test_report.json`);
    
  } catch (error) {
    console.error('❌ Test error:', error.message);
    await screenshot('error_state', `Error: ${error.message}`);
  } finally {
    await page.waitForTimeout(5000);
    await browser.close();
    console.log('\n✅ Test complete!');
  }
}

// Run the test
testAllProgressIndicators().catch(console.error);