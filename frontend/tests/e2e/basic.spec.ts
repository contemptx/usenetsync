describe('Basic GUI Test', () => {
  it('should load the application', async () => {
    // For CI, just verify we can connect
    await browser.url('/');
    
    // Wait for page to load
    await browser.pause(2000);
    
    // Get page title
    const title = await browser.getTitle();
    console.log('Page title:', title);
    
    // Basic assertion
    expect(title).toBeDefined();
  });
});