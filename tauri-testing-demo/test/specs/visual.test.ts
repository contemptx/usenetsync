import { expect } from '@wdio/globals';
import { browser } from '@wdio/globals';

describe('Visual Regression Tests', () => {
    
    beforeEach(async () => {
        // Ensure consistent window size for visual tests
        await browser.setWindowSize(1280, 720);
        await browser.pause(1000); // Wait for any animations to complete
    });
    
    describe('Full Page Screenshots', () => {
        it('should capture the main application view', async () => {
            // Take a full page screenshot
            const result = await browser.checkFullPageScreen('main-view', {
                hideScrollBars: true,
                disableCSSAnimation: true,
                hideElements: ['.timestamp', '.dynamic-content'],
                removeElements: ['.advertisement'],
                fullPageScrollTimeout: 3000,
            });
            
            // Assert that the difference is less than 5%
            expect(result).toBeLessThanOrEqual(5);
        });
        
        it('should capture dark mode if available', async () => {
            // Try to toggle dark mode
            const darkModeToggle = await browser.$('[data-testid="dark-mode-toggle"]');
            if (await darkModeToggle.isExisting()) {
                await darkModeToggle.click();
                await browser.pause(500); // Wait for theme transition
                
                const result = await browser.checkFullPageScreen('dark-mode', {
                    hideScrollBars: true,
                    disableCSSAnimation: true,
                });
                
                expect(result).toBeLessThanOrEqual(5);
            }
        });
    });
    
    describe('Component Screenshots', () => {
        it('should capture header component', async () => {
            const header = await browser.$('header');
            if (await header.isExisting()) {
                const result = await browser.checkElement(header, 'header-component', {
                    removeElements: ['.user-avatar'], // Remove dynamic elements
                });
                expect(result).toBeLessThanOrEqual(2);
            }
        });
        
        it('should capture navigation menu', async () => {
            const nav = await browser.$('nav');
            if (await nav.isExisting()) {
                const result = await browser.checkElement(nav, 'navigation-menu');
                expect(result).toBeLessThanOrEqual(2);
            }
        });
        
        it('should capture form elements', async () => {
            const form = await browser.$('form');
            if (await form.isExisting()) {
                const result = await browser.checkElement(form, 'form-component', {
                    hideElements: ['input[type="password"]'], // Hide sensitive data
                });
                expect(result).toBeLessThanOrEqual(2);
            }
        });
    });
    
    describe('Interactive State Screenshots', () => {
        it('should capture button hover states', async () => {
            const button = await browser.$('button');
            if (await button.isExisting()) {
                // Normal state
                await browser.checkElement(button, 'button-normal');
                
                // Hover state
                await button.moveTo();
                await browser.pause(200);
                const hoverResult = await browser.checkElement(button, 'button-hover');
                expect(hoverResult).toBeLessThanOrEqual(2);
                
                // Focus state
                await button.click();
                await browser.pause(200);
                const focusResult = await browser.checkElement(button, 'button-focus');
                expect(focusResult).toBeLessThanOrEqual(2);
            }
        });
        
        it('should capture input field states', async () => {
            const input = await browser.$('input[type="text"]');
            if (await input.isExisting()) {
                // Empty state
                await browser.checkElement(input, 'input-empty');
                
                // Filled state
                await input.setValue('Test Value');
                const filledResult = await browser.checkElement(input, 'input-filled');
                expect(filledResult).toBeLessThanOrEqual(2);
                
                // Error state (if validation exists)
                await input.setValue('');
                await browser.keys('Tab'); // Trigger validation
                await browser.pause(200);
                const errorResult = await browser.checkElement(input, 'input-error');
                expect(errorResult).toBeLessThanOrEqual(2);
            }
        });
    });
    
    describe('Responsive Design Screenshots', () => {
        const viewports = [
            { width: 320, height: 568, name: 'mobile-small' },
            { width: 768, height: 1024, name: 'tablet' },
            { width: 1920, height: 1080, name: 'desktop-full-hd' },
        ];
        
        for (const viewport of viewports) {
            it(`should capture layout at ${viewport.name} resolution`, async () => {
                await browser.setWindowSize(viewport.width, viewport.height);
                await browser.pause(500); // Wait for responsive adjustments
                
                const result = await browser.checkFullPageScreen(`responsive-${viewport.name}`, {
                    hideScrollBars: true,
                    disableCSSAnimation: true,
                });
                
                expect(result).toBeLessThanOrEqual(5);
            });
        }
    });
    
    describe('Modal and Overlay Screenshots', () => {
        it('should capture modal dialogs', async () => {
            // Try to open a modal
            const modalTrigger = await browser.$('[data-testid="open-modal"]');
            if (await modalTrigger.isExisting()) {
                await modalTrigger.click();
                await browser.pause(500); // Wait for modal animation
                
                const modal = await browser.$('.modal, [role="dialog"]');
                if (await modal.isExisting()) {
                    const result = await browser.checkElement(modal, 'modal-dialog');
                    expect(result).toBeLessThanOrEqual(2);
                    
                    // Close modal
                    await browser.keys('Escape');
                }
            }
        });
        
        it('should capture dropdown menus', async () => {
            const dropdown = await browser.$('[data-testid="dropdown"]');
            if (await dropdown.isExisting()) {
                await dropdown.click();
                await browser.pause(300);
                
                const menu = await browser.$('[role="menu"]');
                if (await menu.isExisting()) {
                    const result = await browser.checkElement(menu, 'dropdown-menu');
                    expect(result).toBeLessThanOrEqual(2);
                }
            }
        });
    });
    
    describe('Animation and Transition Tests', () => {
        it('should capture loading states', async () => {
            const loadingElement = await browser.$('.loading, .spinner');
            if (await loadingElement.isExisting()) {
                // Capture multiple frames of animation
                for (let i = 0; i < 3; i++) {
                    await browser.checkElement(loadingElement, `loading-frame-${i}`);
                    await browser.pause(100);
                }
            }
        });
        
        it('should capture transition states', async () => {
            const transitionElement = await browser.$('[data-testid="transition-element"]');
            if (await transitionElement.isExisting()) {
                // Before transition
                await browser.checkElement(transitionElement, 'transition-before');
                
                // Trigger transition
                await transitionElement.click();
                
                // During transition (multiple captures)
                for (let i = 0; i < 3; i++) {
                    await browser.pause(50);
                    await browser.checkElement(transitionElement, `transition-during-${i}`);
                }
                
                // After transition
                await browser.pause(500);
                const afterResult = await browser.checkElement(transitionElement, 'transition-after');
                expect(afterResult).toBeLessThanOrEqual(2);
            }
        });
    });
    
    describe('Cross-browser Visual Consistency', () => {
        it('should maintain visual consistency across different rendering engines', async () => {
            // This test would run on different browsers in CI
            const browserName = (await browser.capabilities).browserName;
            
            const result = await browser.checkFullPageScreen(`cross-browser-${browserName}`, {
                hideScrollBars: true,
                disableCSSAnimation: true,
            });
            
            expect(result).toBeLessThanOrEqual(5);
            console.log(`Visual test completed for ${browserName}`);
        });
    });
});