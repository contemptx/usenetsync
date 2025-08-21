import { expect } from '@wdio/globals';
import { browser } from '@wdio/globals';

describe('Tauri App E2E Tests', () => {
    
    describe('Application Launch', () => {
        it('should launch the Tauri application', async () => {
            // Wait for app to be ready
            await browser.pause(2000);
            
            // Check if window exists
            const title = await browser.getTitle();
            expect(title).toBeDefined();
            console.log('App launched with title:', title);
        });
        
        it('should have the correct window title', async () => {
            const title = await browser.getTitle();
            expect(title).toContain('Tauri');
        });
    });
    
    describe('UI Interactions', () => {
        it('should find and interact with React components', async () => {
            // Wait for React app to load
            await browser.waitUntil(
                async () => {
                    const elements = await browser.$$('button');
                    return elements.length > 0;
                },
                {
                    timeout: 5000,
                    timeoutMsg: 'Expected buttons to be present after 5s'
                }
            );
            
            // Find and click a button
            const button = await browser.$('button');
            if (await button.isExisting()) {
                await button.click();
                console.log('Button clicked successfully');
            }
        });
        
        it('should handle text input', async () => {
            // Look for input fields
            const inputs = await browser.$$('input');
            if (inputs.length > 0) {
                const firstInput = inputs[0];
                await firstInput.setValue('Test input from WebDriverIO');
                const value = await firstInput.getValue();
                expect(value).toBe('Test input from WebDriverIO');
            }
        });
        
        it('should navigate through the app', async () => {
            // Check for navigation elements
            const links = await browser.$$('a');
            console.log(`Found ${links.length} navigation links`);
            
            // Click first link if available
            if (links.length > 0) {
                const href = await links[0].getAttribute('href');
                await links[0].click();
                await browser.pause(1000);
                console.log(`Navigated to: ${href}`);
            }
        });
    });
    
    describe('Window Management', () => {
        it('should get window dimensions', async () => {
            const windowSize = await browser.getWindowSize();
            expect(windowSize.width).toBeGreaterThan(0);
            expect(windowSize.height).toBeGreaterThan(0);
            console.log('Window size:', windowSize);
        });
        
        it('should resize the window', async () => {
            await browser.setWindowSize(1024, 768);
            const newSize = await browser.getWindowSize();
            expect(newSize.width).toBe(1024);
            expect(newSize.height).toBe(768);
        });
        
        it('should maximize the window', async () => {
            await browser.maximizeWindow();
            const maximizedSize = await browser.getWindowSize();
            expect(maximizedSize.width).toBeGreaterThan(1024);
        });
    });
    
    describe('Keyboard and Mouse Events', () => {
        it('should handle keyboard shortcuts', async () => {
            // Send keyboard shortcut
            await browser.keys(['Control', 'a']);
            await browser.pause(500);
            
            // Test escape key
            await browser.keys('Escape');
            console.log('Keyboard shortcuts tested');
        });
        
        it('should handle mouse movements', async () => {
            const element = await browser.$('body');
            if (await element.isExisting()) {
                // Move mouse to element
                await element.moveTo();
                
                // Perform right click
                await browser.performActions([
                    {
                        type: 'pointer',
                        id: 'mouse',
                        parameters: { pointerType: 'mouse' },
                        actions: [
                            { type: 'pointerDown', button: 2 },
                            { type: 'pointerUp', button: 2 }
                        ]
                    }
                ]);
                console.log('Mouse actions performed');
            }
        });
    });
    
    describe('State Management', () => {
        it('should persist state across interactions', async () => {
            // Check for counter or state element
            const counter = await browser.$('[data-testid="counter"]');
            if (await counter.isExisting()) {
                const initialValue = await counter.getText();
                
                // Click increment button
                const incrementBtn = await browser.$('[data-testid="increment"]');
                if (await incrementBtn.isExisting()) {
                    await incrementBtn.click();
                    await browser.pause(500);
                    
                    const newValue = await counter.getText();
                    expect(newValue).not.toBe(initialValue);
                }
            }
        });
    });
    
    describe('Performance Tests', () => {
        it('should measure app startup time', async () => {
            const startTime = Date.now();
            
            await browser.waitUntil(
                async () => {
                    const ready = await browser.execute(() => {
                        return document.readyState === 'complete';
                    });
                    return ready;
                },
                {
                    timeout: 10000,
                    timeoutMsg: 'App did not load within 10 seconds'
                }
            );
            
            const loadTime = Date.now() - startTime;
            console.log(`App loaded in ${loadTime}ms`);
            expect(loadTime).toBeLessThan(5000); // Should load within 5 seconds
        });
        
        it('should check memory usage', async () => {
            const memoryInfo = await browser.execute(() => {
                if ('memory' in performance) {
                    return (performance as any).memory;
                }
                return null;
            });
            
            if (memoryInfo) {
                console.log('Memory usage:', {
                    usedJSHeapSize: `${(memoryInfo.usedJSHeapSize / 1048576).toFixed(2)} MB`,
                    totalJSHeapSize: `${(memoryInfo.totalJSHeapSize / 1048576).toFixed(2)} MB`
                });
            }
        });
    });
    
    describe('Accessibility Tests', () => {
        it('should have proper ARIA labels', async () => {
            const buttons = await browser.$$('button');
            for (const button of buttons) {
                const ariaLabel = await button.getAttribute('aria-label');
                const text = await button.getText();
                expect(ariaLabel || text).toBeDefined();
            }
        });
        
        it('should be keyboard navigable', async () => {
            // Tab through interactive elements
            await browser.keys('Tab');
            await browser.pause(200);
            
            const activeElement = await browser.execute(() => {
                return document.activeElement?.tagName;
            });
            
            expect(activeElement).toBeDefined();
            console.log('Active element after Tab:', activeElement);
        });
    });
});