const { chromium } = require('playwright');

async function testGUIFolders() {
  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // Enable console logging
  page.on('console', msg => {
    if (msg.type() === 'log') {
      console.log('Browser:', msg.text());
    }
  });
  
  try {
    console.log('='*70);
    console.log(' TESTING FOLDER MANAGEMENT GUI');
    console.log('='*70);
    
    console.log('\n1. Loading app (should bypass license now)...');
    await page.goto('http://localhost:1420', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // Check if we're past the license page
    const pageText = await page.textContent('body');
    const hasLicense = pageText.includes('License');
    const hasFolders = pageText.includes('Folders');
    
    console.log('   Has License text:', hasLicense);
    console.log('   Has Folders link:', hasFolders);
    
    // Navigate to Folders
    console.log('\n2. Navigating to Folders page...');
    await page.goto('http://localhost:1420/folders', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // Check what's on the page
    console.log('\n3. Checking Folders page content...');
    
    // Check for sidebar
    const sidebar = await page.$('.w-80');
    console.log('   ✓ Left sidebar:', sidebar ? 'FOUND' : 'NOT FOUND');
    
    // Check for "Folders" heading
    const foldersHeading = await page.$('h2:has-text("Folders")');
    console.log('   ✓ Folders heading:', foldersHeading ? 'FOUND' : 'NOT FOUND');
    
    // Check for Add Folder button
    const addButton = await page.$('button[title="Add Folder"]');
    console.log('   ✓ Add Folder button:', addButton ? 'FOUND' : 'NOT FOUND');
    
    // Check for tabs
    const tabs = await page.$$('button:has-text("Overview"), button:has-text("Files"), button:has-text("Segments"), button:has-text("Shares"), button:has-text("Actions")');
    console.log(`   ✓ Tabs found: ${tabs.length} (expected 5)`);
    
    // Check for "No folders" message
    const noFolders = pageText.includes('No folders added yet');
    console.log('   ✓ No folders message:', noFolders ? 'SHOWN' : 'NOT SHOWN');
    
    // Test Add Folder functionality
    console.log('\n4. Testing Add Folder button...');
    if (addButton) {
      await addButton.click();
      await page.waitForTimeout(1000);
      
      // Check if dialog opened (it won't in headless, but we can check the API call)
      console.log('   ✓ Add Folder button clicked');
    }
    
    // Check for all expected features
    console.log('\n5. Feature Checklist:');
    const features = {
      'Left Sidebar': await page.$('.w-80'),
      'Database Type Indicator': await page.$('span:has-text("SQLite"), span:has-text("PostgreSQL")'),
      'Folder List Area': await page.$('.divide-y'),
      'Main Content Area': await page.$('.flex-1.bg-gray-50'),
      'Tab Navigation': await page.$('.border-b:has(button)'),
      'Quick Actions': await page.$('button:has-text("Index"), button:has-text("Segment"), button:has-text("Upload"), button:has-text("Share"), button:has-text("Resync"), button:has-text("Delete")'),
      'Select Folder Message': pageText.includes('Select a Folder')
    };
    
    for (const [feature, found] of Object.entries(features)) {
      console.log(`   ${found ? '✓' : '✗'} ${feature}`);
    }
    
    console.log('\n' + '='*70);
    console.log(' TEST COMPLETE');
    console.log('='*70);
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await browser.close();
  }
}

testGUIFolders().catch(console.error);