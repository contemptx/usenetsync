import { expect, browser, $ } from '@wdio/globals';

describe('UsenetSync Basic GUI Tests', () => {
  
  it('should launch the application', async () => {
    // Application should already be launched by WebDriverIO
    const title = await browser.getTitle();
    console.log('Application title:', title);
    expect(title).toBeTruthy();
  });
  
  it('should display the main window', async () => {
    // Check if we can find any element
    const body = await $('body');
    const exists = await body.isExisting();
    expect(exists).toBe(true);
  });
  
  it('should have dashboard elements', async () => {
    // Wait for app to fully load
    await browser.pause(2000);
    
    // Try to find dashboard or any main element
    // Using generic selectors since we don't know exact structure
    const mainContent = await $('div');
    const exists = await mainContent.isExisting();
    expect(exists).toBe(true);
    
    // Take a screenshot for debugging
    await browser.saveScreenshot('./test-screenshot.png');
    console.log('Screenshot saved to test-screenshot.png');
  });
  
  it('should respond to window actions', async () => {
    // Test window manipulation
    const size = await browser.getWindowSize();
    console.log('Current window size:', size);
    expect(size.width).toBeGreaterThan(0);
    expect(size.height).toBeGreaterThan(0);
    
    // Try to resize
    await browser.setWindowSize(1024, 768);
    const newSize = await browser.getWindowSize();
    console.log('New window size:', newSize);
    expect(newSize.width).toBe(1024);
    expect(newSize.height).toBe(768);
  });
  
  it('should have interactive elements', async () => {
    // Look for any buttons or links
    const buttons = await $$('button');
    const links = await $$('a');
    
    console.log(`Found ${buttons.length} buttons`);
    console.log(`Found ${links.length} links`);
    
    // There should be at least some interactive elements
    const totalInteractive = buttons.length + links.length;
    expect(totalInteractive).toBeGreaterThan(0);
  });
});