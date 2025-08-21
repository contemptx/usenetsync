const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ 
    headless: true, 
    args: ['--no-sandbox', '--disable-setuid-sandbox'] 
  });
  const page = await browser.newPage();
  
  await page.goto('http://localhost:1420', { waitUntil: 'networkidle' });
  
  // Get page title
  const title = await page.title();
  console.log('Page Title:', title);
  
  // Get all visible text
  const text = await page.evaluate(() => document.body.innerText);
  console.log('\nPage content (first 800 chars):');
  console.log(text.substring(0, 800));
  
  // Get all links/buttons
  const elements = await page.evaluate(() => {
    const links = Array.from(document.querySelectorAll('a')).map(el => ({
      text: el.textContent.trim(),
      href: el.href
    }));
    const buttons = Array.from(document.querySelectorAll('button')).map(el => ({
      text: el.textContent.trim(),
      disabled: el.disabled
    }));
    return { links, buttons };
  });
  
  console.log('\nLinks found:', elements.links);
  console.log('\nButtons found:', elements.buttons);
  
  // Check current URL
  console.log('\nCurrent URL:', page.url());
  
  // Check for React app root
  const hasRoot = await page.$('#root');
  console.log('Has React root:', !!hasRoot);
  
  // Get navigation structure
  const nav = await page.evaluate(() => {
    const nav = document.querySelector('nav, .nav, .navigation, .sidebar');
    return nav ? nav.textContent.trim() : 'No navigation found';
  });
  console.log('\nNavigation:', nav);
  
  await browser.close();
})().catch(console.error);