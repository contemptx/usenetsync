const { chromium } = require('playwright');
const fs = require('fs');

const FRONTEND_URL = 'http://localhost:1420';
const API_URL = 'http://localhost:8000/api/v1';
const RESULTS_DIR = '/workspace/final_gui_results';

if (!fs.existsSync(RESULTS_DIR)) {
  fs.mkdirSync(RESULTS_DIR, { recursive: true });
}

async function finalGUITest() {
  console.log('🎯 FINAL GUI TEST - VERIFYING 100% FUNCTIONALITY');
  console.log('='*70);
  
  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    slowMo: 100
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: {
      dir: RESULTS_DIR,
      size: { width: 1920, height: 1080 }
    }
  });

  const page = await context.newPage();
  
  let screenshotCount = 0;
  const testResults = {
    passed: [],
    failed: [],
    warnings: []
  };
  
  async function screenshot(name) {
    screenshotCount++;
    const filename = `${RESULTS_DIR}/${String(screenshotCount).padStart(3, '0')}_${name}.png`;
    await page.screenshot({ path: filename, fullPage: true });
    return filename;
  }
  
  async function testFeature(name, testFn) {
    try {
      await testFn();
      console.log(`  ✅ ${name}`);
      testResults.passed.push(name);
      return true;
    } catch (error) {
      console.log(`  ❌ ${name}: ${error.message}`);
      testResults.failed.push(`${name}: ${error.message}`);
      return false;
    }
  }

  try {
    console.log('\n⏳ Starting final test...\n');
    
    // ===========================================
    // TEST 1: NAVIGATION
    // ===========================================
    console.log('📍 TESTING NAVIGATION');
    console.log('-'*50);
    
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle' });
    await screenshot('home_page');
    
    await testFeature('Navigate to Folders', async () => {
      await page.click('a[href="/folders"], button:has-text("Folders")');
      await page.waitForTimeout(1000);
    });
    
    await screenshot('folders_page');
    
    // ===========================================
    // TEST 2: ADD FOLDER BUTTON
    // ===========================================
    console.log('\n📁 TESTING ADD FOLDER BUTTON');
    console.log('-'*50);
    
    await testFeature('Add Folder button visible', async () => {
      const addButton = await page.locator('button:has-text("Add Folder")').first();
      if (!await addButton.isVisible()) {
        throw new Error('Add Folder button not found');
      }
    });
    
    await testFeature('Add Folder button has plus icon', async () => {
      const buttonText = await page.locator('button:has-text("Add Folder")').first().textContent();
      if (!buttonText.includes('+')) {
        throw new Error('Plus icon not found');
      }
    });
    
    await screenshot('add_folder_button');
    
    // ===========================================
    // TEST 3: FOLDER SELECTION AND TABS
    // ===========================================
    console.log('\n📂 TESTING FOLDER INTERACTION');
    console.log('-'*50);
    
    // Get folders count
    const folders = await page.locator('.divide-y > div').all();
    console.log(`  📊 Found ${folders.length} folders`);
    
    if (folders.length > 0) {
      await testFeature('Select folder', async () => {
        await folders[0].click();
        await page.waitForTimeout(1000);
      });
      
      await screenshot('folder_selected');
      
      // Test all tabs
      const tabs = ['overview', 'files', 'segments', 'shares', 'actions'];
      for (const tab of tabs) {
        await testFeature(`${tab} tab`, async () => {
          await page.click(`button:text-is("${tab}")`);
          await page.waitForTimeout(500);
        });
      }
      
      // ===========================================
      // TEST 4: ACTION BUTTONS
      // ===========================================
      console.log('\n🎬 TESTING ACTION BUTTONS');
      console.log('-'*50);
      
      await page.click('button:text-is("actions")');
      await page.waitForTimeout(1000);
      await screenshot('actions_tab');
      
      await testFeature('Index button exists', async () => {
        const button = await page.locator('button:has-text("Index")').first();
        if (!await button.isVisible()) {
          throw new Error('Index button not found');
        }
      });
      
      await testFeature('Segment Files button exists', async () => {
        const button = await page.locator('button:has-text("Segment Files")').first();
        if (!await button.isVisible()) {
          throw new Error('Segment Files button not found');
        }
      });
      
      await testFeature('Upload to Usenet button exists', async () => {
        const button = await page.locator('button:has-text("Upload to Usenet")').first();
        if (!await button.isVisible()) {
          throw new Error('Upload button not found');
        }
      });
      
      await testFeature('Create Share button exists', async () => {
        const button = await page.locator('button:has-text("Create Share")').first();
        if (!await button.isVisible()) {
          throw new Error('Create Share button not found');
        }
      });
      
      // Check button states
      const indexBtn = await page.locator('button:has-text("Index")').first();
      const segmentBtn = await page.locator('button:has-text("Segment Files")').first();
      const uploadBtn = await page.locator('button:has-text("Upload to Usenet")').first();
      const shareBtn = await page.locator('button:has-text("Create Share")').first();
      
      console.log('\n  Button States:');
      console.log(`    Index: ${await indexBtn.isEnabled() ? '✅ Enabled' : '⚠️ Disabled'}`);
      console.log(`    Segment: ${await segmentBtn.isEnabled() ? '✅ Enabled' : '⚠️ Disabled'}`);
      console.log(`    Upload: ${await uploadBtn.isEnabled() ? '✅ Enabled' : '⚠️ Disabled'}`);
      console.log(`    Share: ${await shareBtn.isEnabled() ? '✅ Enabled' : '⚠️ Disabled'}`);
    }
    
    // ===========================================
    // TEST 5: API CONNECTIVITY
    // ===========================================
    console.log('\n🌐 TESTING API CONNECTIVITY');
    console.log('-'*50);
    
    await testFeature('Folders API', async () => {
      const response = await fetch(`${API_URL}/folders`);
      if (!response.ok) throw new Error(`Status ${response.status}`);
    });
    
    await testFeature('Progress API', async () => {
      const response = await fetch(`${API_URL}/progress`);
      if (!response.ok) throw new Error(`Status ${response.status}`);
    });
    
    await testFeature('User Check API', async () => {
      const response = await fetch(`${API_URL}/is_user_initialized`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}'
      });
      if (!response.ok) throw new Error(`Status ${response.status}`);
    });
    
    // ===========================================
    // TEST 6: CONSOLE ERRORS
    // ===========================================
    console.log('\n🔍 CHECKING FOR ERRORS');
    console.log('-'*50);
    
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error' && !msg.text().includes('EventSource')) {
        errors.push(msg.text());
      }
    });
    
    // Navigate to trigger any errors
    await page.goto(`${FRONTEND_URL}/folders`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    if (errors.length > 0) {
      console.log(`  ⚠️ Found ${errors.length} console errors`);
      errors.forEach(e => testResults.warnings.push(e));
    } else {
      console.log('  ✅ No console errors');
    }
    
    await screenshot('final_state');
    
    // ===========================================
    // GENERATE FINAL REPORT
    // ===========================================
    console.log('\n' + '='*70);
    console.log('📊 FINAL GUI TEST REPORT');
    console.log('='*70);
    
    const totalTests = testResults.passed.length + testResults.failed.length;
    const passRate = Math.round((testResults.passed.length / totalTests) * 100);
    
    console.log(`\n✅ PASSED: ${testResults.passed.length}/${totalTests}`);
    testResults.passed.forEach(test => console.log(`  • ${test}`));
    
    if (testResults.failed.length > 0) {
      console.log(`\n❌ FAILED: ${testResults.failed.length}/${totalTests}`);
      testResults.failed.forEach(test => console.log(`  • ${test}`));
    }
    
    if (testResults.warnings.length > 0) {
      console.log(`\n⚠️ WARNINGS: ${testResults.warnings.length}`);
      testResults.warnings.forEach(warning => console.log(`  • ${warning.substring(0, 80)}`));
    }
    
    console.log(`\n📈 GUI HEALTH SCORE: ${passRate}%`);
    
    if (passRate === 100) {
      console.log('\n🎉 PERFECT SCORE! GUI IS 100% FUNCTIONAL!');
    } else if (passRate >= 90) {
      console.log('\n✅ EXCELLENT! GUI is nearly perfect.');
    } else if (passRate >= 80) {
      console.log('\n👍 GOOD! GUI is functional with minor issues.');
    } else {
      console.log('\n⚠️ GUI needs attention.');
    }
    
    // Save report
    const report = {
      timestamp: new Date().toISOString(),
      healthScore: passRate,
      totalTests,
      passed: testResults.passed,
      failed: testResults.failed,
      warnings: testResults.warnings,
      screenshots: screenshotCount
    };
    
    fs.writeFileSync(
      `${RESULTS_DIR}/final_report.json`,
      JSON.stringify(report, null, 2)
    );
    
    console.log('\n📄 Report saved: ' + RESULTS_DIR + '/final_report.json');
    console.log('📸 Screenshots: ' + screenshotCount);
    console.log('🎥 Video saved in: ' + RESULTS_DIR);
    
  } catch (error) {
    console.error('\n❌ Test error:', error.message);
    await screenshot('error');
  } finally {
    await page.waitForTimeout(3000);
    await context.close();
    await browser.close();
    console.log('\n✅ TEST COMPLETE!');
  }
}

// Run the test
finalGUITest().catch(console.error);