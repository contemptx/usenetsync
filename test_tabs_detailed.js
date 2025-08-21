const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  console.log('Testing tabs in detail...\n');
  
  // Quick navigation to folders page
  await page.goto('http://localhost:1420');
  const trial = await page.$('button:has-text("Start Trial")');
  if (trial) await trial.click();
  await page.waitForTimeout(2000);
  await page.click('a:has-text("Folders")');
  await page.waitForTimeout(2000);
  
  // Click on first folder in the list
  console.log('1. Clicking on first folder in list...');
  
  // Try to click on the first folder item in the sidebar
  const firstFolder = await page.evaluate(() => {
    // Find folder items in the sidebar
    const sidebar = document.querySelector('.w-80');
    if (!sidebar) return null;
    
    // Look for folder items (they should be after the "Folders" header)
    const items = sidebar.querySelectorAll('div[class*="hover:bg-gray"], div[class*="cursor-pointer"]');
    
    for (let item of items) {
      const text = item.textContent;
      // Skip if it's the header or empty message
      if (text.includes('Folders') || text.includes('SQLite') || text.includes('No folders')) continue;
      // Check if it looks like a folder item
      if (text.includes('/tmp/') || text.includes('usenet_test')) {
        item.click();
        return text;
      }
    }
    return null;
  });
  
  if (firstFolder) {
    console.log(`   ✓ Clicked on folder: ${firstFolder.substring(0, 50)}`);
    await page.waitForTimeout(1000);
  } else {
    console.log('   ✗ Could not find folder to click');
  }
  
  // Now check for tabs in detail
  console.log('\n2. Searching for tabs...');
  
  const tabInfo = await page.evaluate(() => {
    // Look for all buttons
    const buttons = Array.from(document.querySelectorAll('button'));
    const buttonInfo = buttons.map(b => ({
      text: b.textContent.trim(),
      classes: b.className,
      role: b.getAttribute('role'),
      disabled: b.disabled,
      visible: window.getComputedStyle(b).display !== 'none'
    }));
    
    // Look for tab-like elements
    const tabElements = Array.from(document.querySelectorAll('[role="tab"], [class*="tab"], button'));
    const tabs = tabElements
      .filter(el => {
        const text = el.textContent.trim();
        return ['Overview', 'Files', 'Segments', 'Shares', 'Actions'].some(t => text === t);
      })
      .map(el => ({
        tag: el.tagName,
        text: el.textContent.trim(),
        classes: el.className,
        role: el.getAttribute('role')
      }));
    
    // Check main content area
    const mainContent = document.querySelector('main .flex-1');
    const mainText = mainContent ? mainContent.innerText : '';
    
    return {
      buttons: buttonInfo.filter(b => b.text && b.visible),
      tabs: tabs,
      mainText: mainText.substring(0, 500),
      hasTabText: mainText.includes('Overview') && mainText.includes('Files')
    };
  });
  
  console.log('   All visible buttons:');
  tabInfo.buttons.forEach(b => {
    if (b.text.length < 20) {
      console.log(`   - "${b.text}" (${b.classes.substring(0, 50)}...)`);
    }
  });
  
  console.log('\n   Tab elements found:', tabInfo.tabs.length);
  tabInfo.tabs.forEach(t => {
    console.log(`   - ${t.tag}: "${t.text}" role=${t.role}`);
  });
  
  console.log('\n   Main content has tab text:', tabInfo.hasTabText);
  
  // Try to find tabs using different approach
  console.log('\n3. Looking for tab container...');
  
  const tabContainer = await page.evaluate(() => {
    // Look for the tab list container
    const containers = document.querySelectorAll('[role="tablist"], .tabs, [class*="border-b"]');
    
    for (let container of containers) {
      const text = container.textContent;
      if (text.includes('Overview') && text.includes('Files')) {
        const children = Array.from(container.children);
        return {
          found: true,
          tag: container.tagName,
          classes: container.className,
          childCount: children.length,
          children: children.map(c => ({
            tag: c.tagName,
            text: c.textContent.trim(),
            classes: c.className.substring(0, 50)
          }))
        };
      }
    }
    
    return { found: false };
  });
  
  if (tabContainer.found) {
    console.log(`   ✓ Found tab container: ${tabContainer.tag}`);
    console.log(`   Classes: ${tabContainer.classes}`);
    console.log(`   Children (${tabContainer.childCount}):`);
    tabContainer.children.forEach(c => {
      console.log(`     - ${c.tag}: "${c.text}"`);
    });
  } else {
    console.log('   ✗ Tab container not found');
  }
  
  // Check if tabs are rendered but not as buttons
  console.log('\n4. Checking tab implementation...');
  
  const tabImpl = await page.evaluate(() => {
    const main = document.querySelector('main .flex-1');
    if (!main) return null;
    
    // Get the HTML of the tab area
    const firstDiv = main.querySelector('div');
    if (!firstDiv) return null;
    
    return {
      html: firstDiv.innerHTML.substring(0, 1000),
      hasButtons: firstDiv.querySelectorAll('button').length,
      hasDivs: firstDiv.querySelectorAll('div').length
    };
  });
  
  if (tabImpl) {
    console.log(`   Buttons in tab area: ${tabImpl.hasButtons}`);
    console.log(`   Divs in tab area: ${tabImpl.hasDivs}`);
    console.log(`   HTML preview: ${tabImpl.html.substring(0, 200)}...`);
  }
  
  // Save full page HTML for inspection
  const html = await page.content();
  require('fs').writeFileSync('/tmp/folder_detail_page.html', html);
  console.log('\n5. Full HTML saved to /tmp/folder_detail_page.html');
  
  await browser.close();
})().catch(console.error);