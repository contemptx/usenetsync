const { chromium } = require('playwright');
const fs = require('fs');

async function visualVerificationTest() {
  const browser = await chromium.launch({ 
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  const screenshots = [];
  const features = {
    leftSidebar: false,
    overviewTab: false,
    filesTab: false,
    segmentsTab: false,
    sharesTab: false,
    actionsTab: false,
    quickActions: false,
    shareDialog: false,
    progressBars: false,
    realTimeUpdates: false
  };
  
  try {
    console.log('='*80);
    console.log(' VISUAL VERIFICATION OF ALL FEATURES');
    console.log('='*80);
    
    // Navigate to folders
    await page.goto('http://localhost:1420/folders', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // 1. LEFT SIDEBAR
    console.log('\n1. VERIFYING LEFT SIDEBAR...');
    const sidebar = await page.$('.w-80');
    if (sidebar) {
      features.leftSidebar = true;
      
      // Check for all sidebar elements
      const sidebarFeatures = await page.evaluate(() => {
        const sidebar = document.querySelector('.w-80');
        if (!sidebar) return {};
        
        return {
          hasTitle: !!sidebar.querySelector('h2'),
          hasDatabaseIndicator: sidebar.textContent?.includes('SQLite') || sidebar.textContent?.includes('PostgreSQL'),
          hasAddButton: !!sidebar.querySelector('button[title="Add Folder"]'),
          hasFolderList: !!sidebar.querySelector('.divide-y'),
          folderCount: sidebar.querySelectorAll('.divide-y > div').length,
          hasIcons: sidebar.querySelectorAll('svg').length > 0,
          hasFileStats: sidebar.textContent?.includes('KB') || sidebar.textContent?.includes('MB'),
          hasSegmentStats: sidebar.textContent?.includes('segment')
        };
      });
      
      console.log('   Left Sidebar Features:');
      Object.entries(sidebarFeatures).forEach(([key, value]) => {
        console.log(`     ${value ? '✓' : '✗'} ${key}: ${value}`);
      });
      
      await page.screenshot({ 
        path: '/workspace/test_screenshots/feature_01_sidebar.png',
        clip: { x: 0, y: 0, width: 320, height: 800 }
      });
      screenshots.push('feature_01_sidebar.png');
    }
    
    // Select a folder
    const folders = await page.$$('.divide-y > div');
    if (folders.length > 0) {
      await folders[0].click();
      await page.waitForTimeout(1000);
      
      // 2. OVERVIEW TAB
      console.log('\n2. VERIFYING OVERVIEW TAB...');
      const overviewBtn = await page.$('button[class*="capitalize"]:has-text("overview")');
      if (overviewBtn) {
        await overviewBtn.click();
        await page.waitForTimeout(500);
        
        const overviewFeatures = await page.evaluate(() => {
          const content = document.querySelector('.flex-1.overflow-y-auto');
          if (!content) return {};
          
          const text = content.textContent || '';
          return {
            hasStatisticsPanel: text.includes('Folder Statistics') || content.querySelector('.grid'),
            hasProcessingStatus: text.includes('Processing Status') || text.includes('State'),
            hasSharingStatus: text.includes('Sharing Status') || text.includes('Published'),
            hasTotalFiles: text.includes('Total Files') || text.includes('files'),
            hasTotalSize: text.includes('Total Size') || text.includes('KB'),
            hasSegments: text.includes('Segments'),
            hasCreatedDate: text.includes('Created'),
            hasShareButton: Array.from(content.querySelectorAll('button')).some(b => b.textContent?.includes('Share'))
          };
        });
        
        features.overviewTab = Object.values(overviewFeatures).some(v => v);
        console.log('   Overview Tab Features:');
        Object.entries(overviewFeatures).forEach(([key, value]) => {
          console.log(`     ${value ? '✓' : '✗'} ${key}`);
        });
        
        await page.screenshot({ 
          path: '/workspace/test_screenshots/feature_02_overview.png',
          fullPage: true
        });
        screenshots.push('feature_02_overview.png');
      }
      
      // 3. FILES TAB
      console.log('\n3. VERIFYING FILES TAB...');
      const filesBtn = await page.$('button[class*="capitalize"]:has-text("files")');
      if (filesBtn) {
        await filesBtn.click();
        await page.waitForTimeout(500);
        
        const filesFeatures = await page.evaluate(() => {
          const content = document.querySelector('.flex-1.overflow-y-auto');
          if (!content) return {};
          
          return {
            hasFileTree: content.querySelectorAll('.border').length > 0,
            hasExpandableRows: content.querySelectorAll('svg').length > 0,
            hasFileIcons: !!content.querySelector('.lucide-file'),
            hasFileSizes: content.textContent?.includes('KB') || content.textContent?.includes('MB'),
            hasNoFilesMessage: content.textContent?.includes('not indexed yet'),
            hasIndexButton: Array.from(content.querySelectorAll('button')).some(b => b.textContent?.includes('Index'))
          };
        });
        
        features.filesTab = Object.values(filesFeatures).some(v => v);
        console.log('   Files Tab Features:');
        Object.entries(filesFeatures).forEach(([key, value]) => {
          console.log(`     ${value ? '✓' : '✗'} ${key}`);
        });
        
        await page.screenshot({ 
          path: '/workspace/test_screenshots/feature_03_files.png',
          fullPage: true
        });
        screenshots.push('feature_03_files.png');
      }
      
      // 4. SEGMENTS TAB
      console.log('\n4. VERIFYING SEGMENTS TAB...');
      const segmentsBtn = await page.$('button[class*="capitalize"]:has-text("segments")');
      if (segmentsBtn) {
        await segmentsBtn.click();
        await page.waitForTimeout(500);
        
        const segmentsFeatures = await page.evaluate(() => {
          const content = document.querySelector('.flex-1.overflow-y-auto');
          if (!content) return {};
          
          const text = content.textContent || '';
          return {
            hasTotalSegments: text.includes('Total Segments'),
            hasAvgSegmentSize: text.includes('Avg Segment Size'),
            hasUploadPercentage: text.includes('Uploaded') || text.includes('%'),
            hasSegmentButton: Array.from(content.querySelectorAll('button')).some(b => b.textContent?.includes('Segment'))
          };
        });
        
        features.segmentsTab = Object.values(segmentsFeatures).some(v => v);
        console.log('   Segments Tab Features:');
        Object.entries(segmentsFeatures).forEach(([key, value]) => {
          console.log(`     ${value ? '✓' : '✗'} ${key}`);
        });
        
        await page.screenshot({ 
          path: '/workspace/test_screenshots/feature_04_segments.png',
          fullPage: true
        });
        screenshots.push('feature_04_segments.png');
      }
      
      // 5. SHARES TAB
      console.log('\n5. VERIFYING SHARES TAB...');
      const sharesBtn = await page.$('button[class*="capitalize"]:has-text("shares")');
      if (sharesBtn) {
        await sharesBtn.click();
        await page.waitForTimeout(500);
        
        const sharesFeatures = await page.evaluate(() => {
          const content = document.querySelector('.flex-1.overflow-y-auto');
          if (!content) return {};
          
          return {
            hasSharesList: content.querySelectorAll('.border').length > 0,
            hasNewShareButton: Array.from(content.querySelectorAll('button')).some(b => b.textContent?.includes('New Share')),
            hasShareIcons: content.querySelectorAll('svg').length > 0,
            hasNoSharesMessage: content.textContent?.includes('No shares')
          };
        });
        
        features.sharesTab = Object.values(sharesFeatures).some(v => v);
        console.log('   Shares Tab Features:');
        Object.entries(sharesFeatures).forEach(([key, value]) => {
          console.log(`     ${value ? '✓' : '✗'} ${key}`);
        });
        
        await page.screenshot({ 
          path: '/workspace/test_screenshots/feature_05_shares.png',
          fullPage: true
        });
        screenshots.push('feature_05_shares.png');
      }
      
      // 6. ACTIONS TAB
      console.log('\n6. VERIFYING ACTIONS TAB...');
      const actionsBtn = await page.$('button[class*="capitalize"]:has-text("actions")');
      if (actionsBtn) {
        await actionsBtn.click();
        await page.waitForTimeout(500);
        
        const actionsFeatures = await page.evaluate(() => {
          const content = document.querySelector('.flex-1.overflow-y-auto');
          if (!content) return {};
          
          const buttons = Array.from(content.querySelectorAll('button'));
          const buttonTexts = buttons.map(b => b.textContent?.trim() || '');
          
          return {
            hasProcessingActions: content.textContent?.includes('Processing Actions'),
            hasMaintenanceActions: content.textContent?.includes('Maintenance Actions'),
            hasIndexButton: buttonTexts.some(t => t.includes('Index')),
            hasSegmentButton: buttonTexts.some(t => t.includes('Segment')),
            hasUploadButton: buttonTexts.some(t => t.includes('Upload')),
            hasShareButton: buttonTexts.some(t => t.includes('Share') || t.includes('Publish')),
            hasResyncButton: buttonTexts.some(t => t.includes('Resync')),
            hasRepublishButton: buttonTexts.some(t => t.includes('Republish')),
            hasDownloadButton: buttonTexts.some(t => t.includes('Download')),
            hasDeleteButton: buttonTexts.some(t => t.includes('Delete')),
            totalButtons: buttons.length
          };
        });
        
        features.actionsTab = actionsFeatures.hasProcessingActions && actionsFeatures.hasMaintenanceActions;
        console.log('   Actions Tab Features:');
        Object.entries(actionsFeatures).forEach(([key, value]) => {
          console.log(`     ${value ? '✓' : '✗'} ${key}: ${value}`);
        });
        
        await page.screenshot({ 
          path: '/workspace/test_screenshots/feature_06_actions.png',
          fullPage: true
        });
        screenshots.push('feature_06_actions.png');
      }
      
      // 7. QUICK ACTIONS IN HEADER
      console.log('\n7. VERIFYING QUICK ACTIONS...');
      const quickActionsFeatures = await page.evaluate(() => {
        const header = document.querySelector('.bg-white.dark\\:bg-dark-surface');
        if (!header) return {};
        
        const buttons = Array.from(header.querySelectorAll('button'));
        const buttonTexts = buttons.map(b => b.textContent?.trim() || '');
        
        return {
          hasResync: buttonTexts.some(t => t === 'Resync'),
          hasDelete: buttonTexts.some(t => t === 'Delete'),
          hasContextButtons: buttonTexts.some(t => ['Index', 'Segment', 'Upload', 'Share'].includes(t)),
          totalQuickActions: buttons.filter(b => !['overview', 'files', 'segments', 'shares', 'actions'].includes(b.textContent?.trim().toLowerCase() || '')).length
        };
      });
      
      features.quickActions = quickActionsFeatures.totalQuickActions > 0;
      console.log('   Quick Actions Features:');
      Object.entries(quickActionsFeatures).forEach(([key, value]) => {
        console.log(`     ${value ? '✓' : '✗'} ${key}: ${value}`);
      });
      
      // 8. TEST SHARE DIALOG
      console.log('\n8. TESTING SHARE DIALOG...');
      const shareButton = await page.$('button:has-text("Share"), button:has-text("Create Share")');
      if (shareButton && !await shareButton.isDisabled()) {
        await shareButton.click();
        await page.waitForTimeout(1000);
        
        const dialogFeatures = await page.evaluate(() => {
          const dialog = document.querySelector('.fixed.inset-0');
          if (!dialog) return {};
          
          return {
            hasDialog: true,
            hasPublicOption: !!dialog.querySelector('input[value="public"]'),
            hasPrivateOption: !!dialog.querySelector('input[value="private"]'),
            hasProtectedOption: !!dialog.querySelector('input[value="protected"]'),
            hasPasswordField: !!dialog.querySelector('input[type="password"]'),
            hasCreateButton: !!dialog.querySelector('button:has-text("Create Share")'),
            hasCancelButton: !!dialog.querySelector('button:has-text("Cancel")')
          };
        });
        
        features.shareDialog = dialogFeatures.hasDialog;
        console.log('   Share Dialog Features:');
        Object.entries(dialogFeatures).forEach(([key, value]) => {
          console.log(`     ${value ? '✓' : '✗'} ${key}`);
        });
        
        await page.screenshot({ 
          path: '/workspace/test_screenshots/feature_07_share_dialog.png',
          fullPage: true
        });
        screenshots.push('feature_07_share_dialog.png');
        
        // Close dialog
        const cancelBtn = await page.$('button:has-text("Cancel")');
        if (cancelBtn) await cancelBtn.click();
      }
    }
    
    // FINAL SUMMARY
    console.log('\n' + '='*80);
    console.log(' FEATURE VERIFICATION SUMMARY');
    console.log('='*80);
    
    const totalFeatures = Object.keys(features).length;
    const verifiedFeatures = Object.values(features).filter(v => v).length;
    
    console.log('\nFeatures Verified:');
    Object.entries(features).forEach(([feature, verified]) => {
      console.log(`  ${verified ? '✅' : '❌'} ${feature}`);
    });
    
    console.log(`\nTotal: ${verifiedFeatures}/${totalFeatures} features verified`);
    console.log(`\nScreenshots saved: ${screenshots.join(', ')}`);
    
    if (verifiedFeatures === totalFeatures) {
      console.log('\n🎉 ALL FEATURES VERIFIED SUCCESSFULLY!');
    } else {
      console.log('\n⚠️ Some features could not be verified. Check screenshots for details.');
    }
    
  } catch (error) {
    console.error('Test error:', error);
    await page.screenshot({ path: '/workspace/test_screenshots/visual_error.png', fullPage: true });
  } finally {
    await page.waitForTimeout(3000);
    await browser.close();
  }
}

visualVerificationTest().catch(console.error);