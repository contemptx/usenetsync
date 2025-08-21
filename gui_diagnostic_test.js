const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Configuration
const FRONTEND_URL = 'http://localhost:1420';
const API_URL = 'http://localhost:8000/api/v1';
const DIAGNOSTIC_DIR = '/workspace/gui_diagnostics';

// Ensure directory exists
if (!fs.existsSync(DIAGNOSTIC_DIR)) {
  fs.mkdirSync(DIAGNOSTIC_DIR, { recursive: true });
}

async function comprehensiveGUIDiagnostic() {
  console.log('🔍 COMPREHENSIVE GUI DIAGNOSTIC TEST');
  console.log('='*70);
  console.log('This test will:');
  console.log('  1. Browse through the entire GUI as a real user');
  console.log('  2. Test all interactive elements');
  console.log('  3. Identify and document issues');
  console.log('  4. Capture screenshots and console errors');
  console.log('  5. Generate a detailed diagnostic report');
  console.log('='*70);
  
  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    slowMo: 200 // Slow down for visibility
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: {
      dir: DIAGNOSTIC_DIR,
      size: { width: 1920, height: 1080 }
    }
  });

  const page = await context.newPage();
  
  // Capture console messages
  const consoleMessages = [];
  page.on('console', msg => {
    consoleMessages.push({
      type: msg.type(),
      text: msg.text(),
      location: msg.location()
    });
    if (msg.type() === 'error') {
      console.log(`  ❌ Console Error: ${msg.text()}`);
    }
  });
  
  // Capture network failures
  const networkErrors = [];
  page.on('requestfailed', request => {
    networkErrors.push({
      url: request.url(),
      failure: request.failure()
    });
    console.log(`  ❌ Network Error: ${request.url()} - ${request.failure()?.errorText}`);
  });
  
  let screenshotCount = 0;
  const issues = [];
  const workingFeatures = [];
  
  async function screenshot(name, description) {
    screenshotCount++;
    const filename = `${DIAGNOSTIC_DIR}/${String(screenshotCount).padStart(3, '0')}_${name}.png`;
    await page.screenshot({ path: filename, fullPage: true });
    console.log(`  📸 ${screenshotCount}: ${description}`);
    return filename;
  }
  
  async function testElement(selector, description, action = 'click') {
    try {
      const element = await page.locator(selector).first();
      const isVisible = await element.isVisible({ timeout: 5000 });
      const isEnabled = isVisible ? await element.isEnabled() : false;
      
      if (isVisible && isEnabled) {
        if (action === 'click') {
          await element.click();
        }
        console.log(`  ✅ ${description}: Working`);
        workingFeatures.push(description);
        return true;
      } else {
        const issue = `${description}: ${!isVisible ? 'Not visible' : 'Disabled'}`;
        console.log(`  ⚠️ ${issue}`);
        issues.push(issue);
        return false;
      }
    } catch (error) {
      const issue = `${description}: ${error.message}`;
      console.log(`  ❌ ${issue}`);
      issues.push(issue);
      return false;
    }
  }

  try {
    console.log('\n⏳ Starting diagnostic...');
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // ===========================================
    // TEST 1: INITIAL LOAD
    // ===========================================
    console.log('\n🔍 TEST 1: INITIAL PAGE LOAD');
    console.log('-'*50);
    
    await page.goto(FRONTEND_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await screenshot('initial_load', 'Initial page load');
    
    // Check if page loaded
    const title = await page.title();
    console.log(`  Page Title: ${title}`);
    
    // Check for React app
    const reactRoot = await page.locator('#root, .App, [data-reactroot]').first();
    if (await reactRoot.isVisible()) {
      console.log('  ✅ React app loaded');
      workingFeatures.push('React app initialization');
    } else {
      console.log('  ❌ React app not found');
      issues.push('React app not loading');
    }
    
    // ===========================================
    // TEST 2: NAVIGATION
    // ===========================================
    console.log('\n🔍 TEST 2: NAVIGATION MENU');
    console.log('-'*50);
    
    // Check for navigation elements
    const navItems = [
      { selector: 'a[href="/"], button:has-text("Home")', name: 'Home' },
      { selector: 'a[href="/folders"], button:has-text("Folders")', name: 'Folders' },
      { selector: 'a[href="/upload"], button:has-text("Upload")', name: 'Upload' },
      { selector: 'a[href="/download"], button:has-text("Download")', name: 'Download' },
      { selector: 'a[href="/settings"], button:has-text("Settings")', name: 'Settings' }
    ];
    
    for (const item of navItems) {
      await testElement(item.selector, `Navigation: ${item.name}`);
    }
    
    // ===========================================
    // TEST 3: FOLDERS PAGE
    // ===========================================
    console.log('\n🔍 TEST 3: FOLDERS PAGE');
    console.log('-'*50);
    
    // Navigate to folders
    await page.goto(`${FRONTEND_URL}/folders`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    await screenshot('folders_page', 'Folders page');
    
    // Check for folder list
    const folderList = await page.locator('.divide-y, .folder-list, [class*="folder"]').first();
    if (await folderList.isVisible()) {
      console.log('  ✅ Folder list visible');
      workingFeatures.push('Folder list display');
      
      // Count folders
      const folderItems = await page.locator('.divide-y > div').all();
      console.log(`  📁 Found ${folderItems.length} folders`);
      
      if (folderItems.length > 0) {
        // Click first folder
        await folderItems[0].click();
        await page.waitForTimeout(1000);
        await screenshot('folder_selected', 'Folder selected');
        
        // Check for tabs
        console.log('\n  Testing folder tabs:');
        const tabs = ['overview', 'files', 'segments', 'shares', 'actions'];
        for (const tab of tabs) {
          const tabButton = await page.locator(`button:text-is("${tab}")`).first();
          if (await tabButton.isVisible()) {
            await tabButton.click();
            await page.waitForTimeout(500);
            console.log(`    ✅ ${tab} tab`);
            await screenshot(`tab_${tab}`, `${tab} tab content`);
          } else {
            console.log(`    ❌ ${tab} tab not found`);
            issues.push(`Tab: ${tab} not found`);
          }
        }
        
        // Test action buttons
        console.log('\n  Testing action buttons:');
        await page.click('button:text-is("actions")').catch(() => {});
        await page.waitForTimeout(1000);
        
        const actions = [
          { selector: 'button:has-text("Index")', name: 'Index' },
          { selector: 'button:has-text("Segment")', name: 'Segment' },
          { selector: 'button:has-text("Upload")', name: 'Upload' },
          { selector: 'button:has-text("Create Share")', name: 'Create Share' }
        ];
        
        for (const action of actions) {
          const button = await page.locator(action.selector).first();
          if (await button.isVisible()) {
            const isEnabled = await button.isEnabled();
            console.log(`    ${isEnabled ? '✅' : '⚠️'} ${action.name} button ${isEnabled ? 'enabled' : 'disabled'}`);
            if (isEnabled) {
              workingFeatures.push(`Action: ${action.name}`);
            } else {
              issues.push(`Action: ${action.name} disabled`);
            }
          } else {
            console.log(`    ❌ ${action.name} button not found`);
            issues.push(`Action: ${action.name} not found`);
          }
        }
      } else {
        console.log('  ⚠️ No folders found - creating test folder');
        issues.push('No folders in system');
      }
    } else {
      console.log('  ❌ Folder list not visible');
      issues.push('Folder list not rendering');
    }
    
    // ===========================================
    // TEST 4: ADD FOLDER FUNCTIONALITY
    // ===========================================
    console.log('\n🔍 TEST 4: ADD FOLDER FUNCTIONALITY');
    console.log('-'*50);
    
    // Look for add folder button
    const addFolderBtn = await page.locator('button:has-text("Add Folder"), button:has-text("Add"), button[aria-label*="add"]').first();
    if (await addFolderBtn.isVisible()) {
      console.log('  ✅ Add Folder button found');
      await addFolderBtn.click();
      await page.waitForTimeout(1000);
      await screenshot('add_folder_dialog', 'Add folder dialog');
      
      // Check for dialog elements
      const pathInput = await page.locator('input[type="text"], input[placeholder*="path"], input[name*="path"]').first();
      if (await pathInput.isVisible()) {
        console.log('  ✅ Path input field found');
        workingFeatures.push('Add folder dialog');
      } else {
        console.log('  ❌ Path input field not found');
        issues.push('Add folder dialog incomplete');
      }
      
      // Close dialog
      await page.keyboard.press('Escape');
    } else {
      console.log('  ❌ Add Folder button not found');
      issues.push('Add Folder button missing');
    }
    
    // ===========================================
    // TEST 5: API CONNECTIVITY
    // ===========================================
    console.log('\n🔍 TEST 5: API CONNECTIVITY');
    console.log('-'*50);
    
    // Test API endpoints
    const apiTests = [
      { endpoint: '/folders', method: 'GET', name: 'Get Folders' },
      { endpoint: '/is_user_initialized', method: 'POST', name: 'User Check' },
      { endpoint: '/progress', method: 'GET', name: 'Progress Status' }
    ];
    
    for (const test of apiTests) {
      try {
        const response = await fetch(`${API_URL}${test.endpoint}`, {
          method: test.method,
          headers: { 'Content-Type': 'application/json' },
          body: test.method === 'POST' ? '{}' : undefined
        });
        
        if (response.ok) {
          console.log(`  ✅ API: ${test.name} - Status ${response.status}`);
          workingFeatures.push(`API: ${test.name}`);
        } else {
          console.log(`  ⚠️ API: ${test.name} - Status ${response.status}`);
          issues.push(`API: ${test.name} returned ${response.status}`);
        }
      } catch (error) {
        console.log(`  ❌ API: ${test.name} - ${error.message}`);
        issues.push(`API: ${test.name} failed`);
      }
    }
    
    // ===========================================
    // TEST 6: PROGRESS INDICATORS
    // ===========================================
    console.log('\n🔍 TEST 6: PROGRESS INDICATORS');
    console.log('-'*50);
    
    // Check for progress bar component
    const progressBar = await page.locator('[role="progressbar"], .progress-bar, [class*="progress"]').first();
    if (await progressBar.isVisible()) {
      console.log('  ✅ Progress bar component found');
      workingFeatures.push('Progress bar component');
    } else {
      console.log('  ℹ️ No active progress bars (expected if no operations running)');
    }
    
    // ===========================================
    // GENERATE DIAGNOSTIC REPORT
    // ===========================================
    console.log('\n' + '='*70);
    console.log('📊 GUI DIAGNOSTIC REPORT');
    console.log('='*70);
    
    console.log('\n✅ WORKING FEATURES (' + workingFeatures.length + '):');
    workingFeatures.forEach(feature => {
      console.log(`  • ${feature}`);
    });
    
    console.log('\n❌ ISSUES FOUND (' + issues.length + '):');
    if (issues.length > 0) {
      issues.forEach(issue => {
        console.log(`  • ${issue}`);
      });
    } else {
      console.log('  None - GUI is fully functional!');
    }
    
    console.log('\n🔍 CONSOLE ERRORS (' + consoleMessages.filter(m => m.type === 'error').length + '):');
    consoleMessages.filter(m => m.type === 'error').forEach(msg => {
      console.log(`  • ${msg.text}`);
    });
    
    console.log('\n🌐 NETWORK ERRORS (' + networkErrors.length + '):');
    networkErrors.forEach(error => {
      console.log(`  • ${error.url}: ${error.failure?.errorText}`);
    });
    
    // Save detailed report
    const report = {
      timestamp: new Date().toISOString(),
      url: FRONTEND_URL,
      workingFeatures,
      issues,
      consoleErrors: consoleMessages.filter(m => m.type === 'error'),
      networkErrors,
      screenshots: screenshotCount,
      summary: {
        totalTests: workingFeatures.length + issues.length,
        passed: workingFeatures.length,
        failed: issues.length,
        healthScore: Math.round((workingFeatures.length / (workingFeatures.length + issues.length)) * 100)
      }
    };
    
    fs.writeFileSync(
      `${DIAGNOSTIC_DIR}/diagnostic_report.json`,
      JSON.stringify(report, null, 2)
    );
    
    console.log('\n📈 HEALTH SCORE: ' + report.summary.healthScore + '%');
    console.log('\n📄 DETAILED REPORT SAVED:');
    console.log(`  ${DIAGNOSTIC_DIR}/diagnostic_report.json`);
    console.log('\n📸 SCREENSHOTS: ' + screenshotCount);
    console.log(`  Location: ${DIAGNOSTIC_DIR}/*.png`);
    
    // Provide recommendations
    console.log('\n💡 RECOMMENDATIONS:');
    if (issues.length > 0) {
      console.log('  Based on the issues found, here are the recommended fixes:');
      if (issues.some(i => i.includes('React app'))) {
        console.log('  • Check if frontend dev server is running');
        console.log('  • Verify React build is successful');
      }
      if (issues.some(i => i.includes('API'))) {
        console.log('  • Check backend server is running');
        console.log('  • Verify API endpoints are implemented');
      }
      if (issues.some(i => i.includes('button'))) {
        console.log('  • Review button state management');
        console.log('  • Check conditional rendering logic');
      }
    } else {
      console.log('  • GUI is working well!');
      console.log('  • Consider adding more features');
    }
    
  } catch (error) {
    console.error('\n❌ Diagnostic error:', error.message);
    await screenshot('error', error.message);
  } finally {
    await page.waitForTimeout(5000);
    await context.close();
    await browser.close();
    
    console.log('\n✅ DIAGNOSTIC COMPLETE!');
  }
}

// Run the diagnostic
comprehensiveGUIDiagnostic().catch(console.error);