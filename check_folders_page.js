const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  console.log('1. Loading app...');
  await page.goto('http://localhost:1420');
  
  // Start trial
  const trial = await page.$('button:has-text("Start Trial")');
  if (trial) {
    await trial.click();
    console.log('2. Started trial');
  }
  await page.waitForTimeout(2000);
  
  // Navigate to Folders
  const folders = await page.$('a:has-text("Folders")');
  if (folders) {
    await folders.click();
    console.log('3. Navigated to Folders');
  }
  await page.waitForTimeout(2000);
  
  // Get the page content
  const content = await page.evaluate(() => {
    return {
      title: document.title,
      url: window.location.href,
      bodyText: document.body.innerText.substring(0, 1500),
      hasReactRoot: !!document.querySelector('#root'),
      mainContent: document.querySelector('main, .main, [role="main"]')?.innerHTML?.substring(0, 500),
      buttons: Array.from(document.querySelectorAll('button')).map(b => b.textContent.trim()),
      divClasses: Array.from(document.querySelectorAll('div')).map(d => d.className).filter(c => c.includes('folder') || c.includes('Folder')).slice(0, 10)
    };
  });
  
  console.log('\n4. Page Analysis:');
  console.log('   URL:', content.url);
  console.log('   Has React root:', content.hasReactRoot);
  console.log('   Buttons found:', content.buttons);
  console.log('   Folder-related divs:', content.divClasses);
  console.log('\n5. Page content:');
  console.log(content.bodyText);
  
  // Save page HTML for inspection
  const html = await page.content();
  require('fs').writeFileSync('/tmp/folders_page.html', html);
  console.log('\n6. Full HTML saved to /tmp/folders_page.html');
  
  await browser.close();
})();