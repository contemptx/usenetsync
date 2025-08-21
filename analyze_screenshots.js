const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Configuration
const FRONTEND_URL = 'http://localhost:1420';
const API_URL = 'http://localhost:8000/api/v1';
const REPORT_DIR = '/workspace/progress_analysis';

// Ensure report directory exists
if (!fs.existsSync(REPORT_DIR)) {
  fs.mkdirSync(REPORT_DIR, { recursive: true });
}

async function analyzeProgress() {
  console.log('🔍 ANALYZING ACTUAL PAGE CONTENT FOR PROGRESS INDICATORS');
  console.log('='*70);
  
  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 }
  });

  const analysis = {
    timestamp: new Date().toISOString(),
    tests: []
  };

  try {
    // Navigate to folders page
    console.log('\n1️⃣ NAVIGATING TO APPLICATION');
    await page.goto(`${FRONTEND_URL}/folders`, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // Get page HTML to analyze
    const pageHTML = await page.content();
    fs.writeFileSync(`${REPORT_DIR}/initial_page.html`, pageHTML);
    
    // Check what's actually on the page
    const visibleElements = await page.evaluate(() => {
      const elements = {
        buttons: [],
        spinners: [],
        progressBars: [],
        loadingTexts: [],
        animations: []
      };
      
      // Find all buttons
      document.querySelectorAll('button').forEach(btn => {
        elements.buttons.push({
          text: btn.textContent.trim(),
          disabled: btn.disabled,
          className: btn.className
        });
      });
      
      // Find spinners (common spinner classes)
      const spinnerSelectors = [
        '.animate-spin',
        '.spinner',
        '.loading',
        '.animate-pulse',
        '[role="status"]'
      ];
      
      spinnerSelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach(el => {
          elements.spinners.push({
            selector: selector,
            className: el.className,
            visible: el.offsetParent !== null
          });
        });
      });
      
      // Find progress bars
      const progressSelectors = [
        '[role="progressbar"]',
        '.progress',
        '.progress-bar',
        '[class*="progress"]'
      ];
      
      progressSelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach(el => {
          elements.progressBars.push({
            selector: selector,
            className: el.className,
            visible: el.offsetParent !== null,
            value: el.getAttribute('aria-valuenow') || el.style.width
          });
        });
      });
      
      // Find loading text
      const loadingKeywords = ['loading', 'processing', 'indexing', 'uploading', 'downloading', 'segmenting'];
      loadingKeywords.forEach(keyword => {
        const xpath = `//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '${keyword}')]`;
        const result = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
        for (let i = 0; i < result.snapshotLength; i++) {
          const node = result.snapshotItem(i);
          if (node.offsetParent !== null) {
            elements.loadingTexts.push({
              text: node.textContent.trim(),
              visible: true
            });
          }
        }
      });
      
      // Find CSS animations
      document.querySelectorAll('*').forEach(el => {
        const computed = window.getComputedStyle(el);
        if (computed.animationName !== 'none' || computed.transition !== 'none 0s ease 0s') {
          elements.animations.push({
            tagName: el.tagName,
            className: el.className,
            animation: computed.animationName,
            transition: computed.transition
          });
        }
      });
      
      return elements;
    });
    
    console.log('\n📊 INITIAL PAGE ANALYSIS:');
    console.log(`  Buttons found: ${visibleElements.buttons.length}`);
    console.log(`  Spinners found: ${visibleElements.spinners.length}`);
    console.log(`  Progress bars found: ${visibleElements.progressBars.length}`);
    console.log(`  Loading texts found: ${visibleElements.loadingTexts.length}`);
    console.log(`  Animations found: ${visibleElements.animations.length}`);
    
    analysis.tests.push({
      name: 'Initial Page State',
      elements: visibleElements
    });
    
    // Create a test folder
    console.log('\n2️⃣ CREATING TEST FOLDER');
    const testDir = '/workspace/analyze_test_' + Date.now();
    fs.mkdirSync(testDir, { recursive: true });
    fs.writeFileSync(path.join(testDir, 'test.txt'), 'x'.repeat(50000));
    
    const addResponse = await fetch(`${API_URL}/add_folder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        path: testDir,
        name: 'Progress Analysis Test'
      })
    });
    
    const addData = await addResponse.json();
    const folderId = addData.folder_id;
    console.log(`  Folder created: ${folderId}`);
    
    // Reload and select folder
    await page.reload();
    await page.waitForTimeout(2000);
    
    const folderItem = await page.locator('.divide-y > div').first();
    await folderItem.click();
    await page.waitForTimeout(1000);
    
    // Go to actions tab
    await page.click('button:text-is("actions")');
    await page.waitForTimeout(1000);
    
    // Now test indexing with detailed monitoring
    console.log('\n3️⃣ TESTING INDEXING OPERATION');
    
    const indexButton = await page.locator('button:has-text("Index")').first();
    if (await indexButton.isVisible()) {
      console.log('  Starting index operation...');
      
      // Set up monitoring before clicking
      const progressStates = [];
      let captureInterval;
      
      const captureProgress = async () => {
        const state = await page.evaluate(() => {
          const result = {
            timestamp: Date.now(),
            spinners: document.querySelectorAll('.animate-spin, .animate-pulse').length,
            progressBars: document.querySelectorAll('[role="progressbar"], .progress').length,
            loadingTexts: [],
            disabledButtons: []
          };
          
          // Check for loading text
          const textElements = document.querySelectorAll('*');
          textElements.forEach(el => {
            if (el.textContent && el.textContent.match(/loading|indexing|processing/i)) {
              result.loadingTexts.push(el.textContent.trim());
            }
          });
          
          // Check for disabled buttons
          document.querySelectorAll('button:disabled').forEach(btn => {
            result.disabledButtons.push(btn.textContent.trim());
          });
          
          return result;
        });
        
        progressStates.push(state);
        return state;
      };
      
      // Start capturing
      captureInterval = setInterval(async () => {
        const state = await captureProgress();
        if (state.spinners > 0 || state.progressBars > 0 || state.loadingTexts.length > 0) {
          console.log(`  📍 Progress detected: Spinners=${state.spinners}, Bars=${state.progressBars}, Texts=${state.loadingTexts.length}`);
        }
      }, 200);
      
      // Click the button
      await indexButton.click();
      
      // Capture for 5 seconds
      await page.waitForTimeout(5000);
      
      // Stop capturing
      clearInterval(captureInterval);
      
      console.log(`  Captured ${progressStates.length} states during operation`);
      
      // Analyze captured states
      const hasProgress = progressStates.some(state => 
        state.spinners > 0 || 
        state.progressBars > 0 || 
        state.loadingTexts.length > 0
      );
      
      analysis.tests.push({
        name: 'Indexing Operation',
        hasProgress: hasProgress,
        states: progressStates
      });
      
      if (hasProgress) {
        console.log('  ✅ PROGRESS INDICATORS DETECTED!');
      } else {
        console.log('  ❌ NO PROGRESS INDICATORS FOUND');
      }
    }
    
    // Generate detailed HTML report
    console.log('\n4️⃣ GENERATING PROOF REPORT');
    
    const htmlReport = `
<!DOCTYPE html>
<html>
<head>
  <title>Progress Analysis Report</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    h1 { color: #333; }
    .test { border: 1px solid #ddd; padding: 15px; margin: 20px 0; }
    .success { background: #d4edda; }
    .failure { background: #f8d7da; }
    .state { background: #f0f0f0; padding: 10px; margin: 5px 0; }
    pre { background: #f5f5f5; padding: 10px; overflow-x: auto; }
    .timestamp { color: #666; font-size: 0.9em; }
  </style>
</head>
<body>
  <h1>Progress Indicator Analysis Report</h1>
  <p class="timestamp">Generated: ${analysis.timestamp}</p>
  
  <h2>Test Results</h2>
  ${analysis.tests.map(test => `
    <div class="test ${test.hasProgress ? 'success' : 'failure'}">
      <h3>${test.name}</h3>
      ${test.elements ? `
        <h4>Elements Found:</h4>
        <ul>
          <li>Buttons: ${test.elements.buttons.length}</li>
          <li>Spinners: ${test.elements.spinners.length}</li>
          <li>Progress Bars: ${test.elements.progressBars.length}</li>
          <li>Loading Texts: ${test.elements.loadingTexts.length}</li>
          <li>Animations: ${test.elements.animations.length}</li>
        </ul>
        ${test.elements.spinners.length > 0 ? `
          <h4>Spinner Details:</h4>
          <pre>${JSON.stringify(test.elements.spinners, null, 2)}</pre>
        ` : ''}
        ${test.elements.loadingTexts.length > 0 ? `
          <h4>Loading Text Details:</h4>
          <pre>${JSON.stringify(test.elements.loadingTexts, null, 2)}</pre>
        ` : ''}
      ` : ''}
      ${test.states ? `
        <h4>Progress States Captured: ${test.states.length}</h4>
        <div style="max-height: 400px; overflow-y: auto;">
          ${test.states.filter(s => s.spinners > 0 || s.loadingTexts.length > 0).map((state, i) => `
            <div class="state">
              <strong>State ${i + 1}:</strong>
              Spinners: ${state.spinners}, 
              Progress Bars: ${state.progressBars},
              Loading Texts: ${state.loadingTexts.length}
              ${state.loadingTexts.length > 0 ? `
                <br>Texts: ${state.loadingTexts.join(', ')}
              ` : ''}
            </div>
          `).join('')}
        </div>
      ` : ''}
    </div>
  `).join('')}
  
  <h2>Raw Data</h2>
  <pre>${JSON.stringify(analysis, null, 2)}</pre>
</body>
</html>
    `;
    
    fs.writeFileSync(`${REPORT_DIR}/progress_analysis.html`, htmlReport);
    fs.writeFileSync(`${REPORT_DIR}/progress_analysis.json`, JSON.stringify(analysis, null, 2));
    
    console.log('\n' + '='*70);
    console.log('📁 ANALYSIS COMPLETE');
    console.log(`  HTML Report: ${REPORT_DIR}/progress_analysis.html`);
    console.log(`  JSON Data: ${REPORT_DIR}/progress_analysis.json`);
    console.log(`  Page HTML: ${REPORT_DIR}/initial_page.html`);
    
  } catch (error) {
    console.error('❌ Analysis error:', error.message);
    analysis.error = error.message;
  } finally {
    await browser.close();
  }
  
  return analysis;
}

// Run the analysis
analyzeProgress().catch(console.error);