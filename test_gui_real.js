const { chromium } = require('playwright');

async function testGUI() {
  console.log('='.repeat(60));
  console.log('TESTING ACTUAL GUI FUNCTIONALITY');
  console.log('='.repeat(60));

  const browser = await chromium.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Enable console logging
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('Browser Console Error:', msg.text());
    }
  });

  // Monitor network requests
  page.on('request', request => {
    if (request.url().includes('/api/')) {
      console.log(`API Request: ${request.method()} ${request.url()}`);
      if (request.postData()) {
        console.log(`  Body: ${request.postData()}`);
      }
    }
  });

  page.on('response', response => {
    if (response.url().includes('/api/')) {
      console.log(`API Response: ${response.status()} ${response.url()}`);
    }
  });

  try {
    console.log('\n1. Loading the application...');
    await page.goto('http://localhost:1420', { waitUntil: 'networkidle' });
    console.log('   ✓ Page loaded');

    // Take screenshot of initial state
    await page.screenshot({ path: '/tmp/gui_initial.png' });
    console.log('   ✓ Screenshot saved to /tmp/gui_initial.png');

    // Check what's visible on the page
    console.log('\n2. Checking page structure...');
    
    // Check for navigation
    const navItems = await page.$$eval('nav a, [role="navigation"] a, .nav-link, .sidebar a', links => 
      links.map(link => link.textContent.trim())
    );
    console.log('   Navigation items found:', navItems);

    // Navigate to Folders page
    console.log('\n3. Navigating to Folders page...');
    
    // Try different selectors for the Folders link
    const foldersLink = await page.$('text=Folders') || 
                       await page.$('text=Folder') ||
                       await page.$('[href*="folder"]') ||
                       await page.$('a:has-text("Folder")');
    
    if (foldersLink) {
      await foldersLink.click();
      await page.waitForTimeout(1000);
      console.log('   ✓ Clicked on Folders link');
    } else {
      console.log('   ⚠ Could not find Folders link, checking current page...');
    }

    // Check for tabs
    console.log('\n4. Checking for tabs...');
    const tabs = await page.$$eval('button[role="tab"], [class*="tab"], button:has-text("Overview"), button:has-text("Files")', tabs => 
      tabs.map(tab => tab.textContent.trim())
    );
    console.log('   Tabs found:', tabs);

    // Check for the Add Folder button
    console.log('\n5. Looking for Add Folder button...');
    const addFolderButton = await page.$('button:has-text("Add Folder")') ||
                           await page.$('button:has([class*="FolderOpen"])') ||
                           await page.$('button:has-text("Add")');
    
    if (addFolderButton) {
      console.log('   ✓ Found Add Folder button');
      
      // Get button properties
      const buttonText = await addFolderButton.textContent();
      const isDisabled = await addFolderButton.isDisabled();
      console.log(`   Button text: "${buttonText}", Disabled: ${isDisabled}`);
      
      // Try clicking it
      console.log('\n6. Clicking Add Folder button...');
      await addFolderButton.click();
      await page.waitForTimeout(2000);
      
      // Check if a dialog appeared
      const dialog = await page.$('[role="dialog"], .modal, [class*="dialog"]');
      if (dialog) {
        console.log('   ✓ Dialog appeared');
        await page.screenshot({ path: '/tmp/gui_dialog.png' });
      } else {
        console.log('   ⚠ No dialog appeared (may be file picker)');
      }
    } else {
      console.log('   ✗ Add Folder button not found');
    }

    // Check for folder list
    console.log('\n7. Checking for folder list...');
    const folderItems = await page.$$eval('[class*="folder"], [class*="Folder"]', items => 
      items.map(item => ({
        text: item.textContent.trim().substring(0, 100),
        classes: item.className
      }))
    );
    
    if (folderItems.length > 0) {
      console.log(`   Found ${folderItems.length} folder-related elements`);
      folderItems.slice(0, 3).forEach(item => {
        console.log(`   - ${item.text}`);
      });
    } else {
      console.log('   No folders in list');
    }

    // Check the main content area
    console.log('\n8. Checking main content area...');
    const mainContent = await page.$eval('main, [role="main"], .main-content, .flex-1', el => {
      return {
        text: el.textContent.trim().substring(0, 200),
        hasOverviewTab: el.textContent.includes('Overview'),
        hasFilesTab: el.textContent.includes('Files'),
        hasSegmentsTab: el.textContent.includes('Segments'),
        hasSharesTab: el.textContent.includes('Shares'),
        hasActionsTab: el.textContent.includes('Actions')
      };
    }).catch(() => null);
    
    if (mainContent) {
      console.log('   Main content found:');
      console.log('   - Has Overview tab:', mainContent.hasOverviewTab);
      console.log('   - Has Files tab:', mainContent.hasFilesTab);
      console.log('   - Has Segments tab:', mainContent.hasSegmentsTab);
      console.log('   - Has Shares tab:', mainContent.hasSharesTab);
      console.log('   - Has Actions tab:', mainContent.hasActionsTab);
    }

    // Test the Overview tab if present
    if (mainContent?.hasOverviewTab) {
      console.log('\n9. Testing Overview tab...');
      const overviewTab = await page.$('button:has-text("Overview")');
      if (overviewTab) {
        await overviewTab.click();
        await page.waitForTimeout(500);
        
        // Check for statistics
        const stats = await page.$$eval('[class*="stat"], dl', elements => 
          elements.map(el => el.textContent.trim()).filter(t => t.length > 0)
        );
        console.log('   Statistics found:', stats.length > 0 ? 'Yes' : 'No');
      }
    }

    // Test the Files tab if present
    if (mainContent?.hasFilesTab) {
      console.log('\n10. Testing Files tab...');
      const filesTab = await page.$('button:has-text("Files")');
      if (filesTab) {
        await filesTab.click();
        await page.waitForTimeout(500);
        await page.screenshot({ path: '/tmp/gui_files_tab.png' });
        console.log('   ✓ Files tab screenshot saved');
      }
    }

    // Final screenshot
    await page.screenshot({ path: '/tmp/gui_final.png', fullPage: true });
    console.log('\n✓ Final full-page screenshot saved to /tmp/gui_final.png');

  } catch (error) {
    console.error('\n✗ Error during testing:', error);
    await page.screenshot({ path: '/tmp/gui_error.png' });
  } finally {
    await browser.close();
  }

  console.log('\n' + '='.repeat(60));
  console.log('GUI TEST COMPLETE');
  console.log('='.repeat(60));
}

testGUI().catch(console.error);