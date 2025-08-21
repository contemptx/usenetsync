import { expect } from '@wdio/globals';

describe('Visual Regression Tests', () => {
  let mainWindow: WebdriverIO.Browser;
  
  before(async () => {
    mainWindow = await browser;
    await mainWindow.maximizeWindow();
    await browser.pause(2000);
  });
  
  describe('Dashboard Visual Tests', () => {
    it('should match dashboard layout', async () => {
      const dashboard = await mainWindow.$('[data-testid="dashboard"]');
      await expect(dashboard).toBeDisplayed();
      
      // Full page screenshot
      await browser.checkScreen('dashboard-full');
      
      // Component screenshots
      const statsWidget = await mainWindow.$('[data-testid="system-stats"]');
      await browser.checkElement(await statsWidget, 'dashboard-stats-widget');
      
      const recentActivity = await mainWindow.$('[data-testid="recent-activity"]');
      if (await recentActivity.isDisplayed()) {
        await browser.checkElement(await recentActivity, 'dashboard-recent-activity');
      }
    });
    
    it('should match dashboard in dark mode', async () => {
      // Toggle dark mode
      const darkModeToggle = await mainWindow.$('[data-testid="dark-mode-toggle"]');
      await darkModeToggle.click();
      await browser.pause(500);
      
      await browser.checkScreen('dashboard-dark-mode');
      
      // Toggle back
      await darkModeToggle.click();
      await browser.pause(500);
    });
  });
  
  describe('Folder Management Visual Tests', () => {
    before(async () => {
      const folderNav = await mainWindow.$('[data-testid="nav-folders"]');
      await folderNav.click();
      await browser.pause(500);
    });
    
    it('should match folder list layout', async () => {
      const folderPage = await mainWindow.$('[data-testid="folder-management"]');
      await expect(folderPage).toBeDisplayed();
      
      await browser.checkScreen('folder-management-empty');
      
      // Add a test folder for visual testing
      await browser.execute(() => {
        window.postMessage({
          type: 'test-data',
          folders: [
            {
              id: 'test-1',
              name: 'Documents',
              path: '/home/user/Documents',
              size: 1024 * 1024 * 150,
              files: 42,
              status: 'indexed'
            },
            {
              id: 'test-2',
              name: 'Pictures',
              path: '/home/user/Pictures',
              size: 1024 * 1024 * 500,
              files: 128,
              status: 'segmented'
            }
          ]
        }, '*');
      });
      
      await browser.pause(500);
      await browser.checkScreen('folder-management-with-folders');
    });
    
    it('should match folder details view', async () => {
      const firstFolder = await mainWindow.$('[data-testid="folder-item"]');
      if (await firstFolder.isDisplayed()) {
        await firstFolder.click();
        await browser.pause(500);
        
        const folderDetails = await mainWindow.$('[data-testid="folder-details"]');
        if (await folderDetails.isDisplayed()) {
          await browser.checkElement(await folderDetails, 'folder-details-view');
        }
      }
    });
  });
  
  describe('Share Creation Visual Tests', () => {
    before(async () => {
      const sharesNav = await mainWindow.$('[data-testid="nav-shares"]');
      await sharesNav.click();
      await browser.pause(500);
    });
    
    it('should match share creation dialog', async () => {
      const createButton = await mainWindow.$('[data-testid="create-share-btn"]');
      await createButton.click();
      await browser.pause(500);
      
      const shareDialog = await mainWindow.$('[data-testid="share-dialog"]');
      if (await shareDialog.isDisplayed()) {
        await browser.checkElement(await shareDialog, 'share-creation-dialog');
      }
      
      // Close dialog
      const cancelButton = await mainWindow.$('[data-testid="cancel-share-btn"]');
      if (await cancelButton.isDisplayed()) {
        await cancelButton.click();
        await browser.pause(500);
      }
    });
    
    it('should match share list view', async () => {
      // Add test shares
      await browser.execute(() => {
        window.postMessage({
          type: 'test-data',
          shares: [
            {
              id: 'share-1',
              name: 'Public Document Share',
              type: 'public',
              created: new Date().toISOString(),
              downloads: 15
            },
            {
              id: 'share-2',
              name: 'Private Team Share',
              type: 'private',
              created: new Date().toISOString(),
              downloads: 3
            },
            {
              id: 'share-3',
              name: 'Protected Archive',
              type: 'protected',
              created: new Date().toISOString(),
              downloads: 7
            }
          ]
        }, '*');
      });
      
      await browser.pause(500);
      await browser.checkScreen('shares-list-view');
    });
  });
  
  describe('Upload/Download Visual Tests', () => {
    it('should match upload progress view', async () => {
      const uploadsNav = await mainWindow.$('[data-testid="nav-uploads"]');
      await uploadsNav.click();
      await browser.pause(500);
      
      // Simulate upload progress
      await browser.execute(() => {
        window.postMessage({
          type: 'test-data',
          uploads: [
            {
              id: 'upload-1',
              name: 'Large Archive.zip',
              progress: 45,
              speed: '2.5 MB/s',
              timeRemaining: '5 min'
            }
          ]
        }, '*');
      });
      
      await browser.pause(500);
      await browser.checkScreen('upload-in-progress-view');
    });
    
    it('should match download queue view', async () => {
      const downloadsNav = await mainWindow.$('[data-testid="nav-downloads"]');
      await downloadsNav.click();
      await browser.pause(500);
      
      // Simulate download queue
      await browser.execute(() => {
        window.postMessage({
          type: 'test-data',
          downloads: [
            {
              id: 'dl-1',
              name: 'Project Files',
              progress: 78,
              speed: '5.2 MB/s',
              status: 'downloading'
            },
            {
              id: 'dl-2',
              name: 'Media Collection',
              progress: 0,
              status: 'queued'
            },
            {
              id: 'dl-3',
              name: 'Documents',
              progress: 100,
              status: 'completed'
            }
          ]
        }, '*');
      });
      
      await browser.pause(500);
      await browser.checkScreen('download-queue-view');
    });
  });
  
  describe('Settings Visual Tests', () => {
    before(async () => {
      const settingsNav = await mainWindow.$('[data-testid="nav-settings"]');
      await settingsNav.click();
      await browser.pause(500);
    });
    
    it('should match settings general tab', async () => {
      await browser.checkScreen('settings-general-tab');
    });
    
    it('should match settings NNTP tab', async () => {
      const nntpTab = await mainWindow.$('[data-testid="settings-nntp-tab"]');
      await nntpTab.click();
      await browser.pause(500);
      
      await browser.checkScreen('settings-nntp-tab');
    });
    
    it('should match settings security tab', async () => {
      const securityTab = await mainWindow.$('[data-testid="settings-security-tab"]');
      if (await securityTab.isDisplayed()) {
        await securityTab.click();
        await browser.pause(500);
        
        await browser.checkScreen('settings-security-tab');
      }
    });
  });
  
  describe('Error States Visual Tests', () => {
    it('should match network error state', async () => {
      // Simulate network error
      await browser.execute(() => {
        window.postMessage({
          type: 'error',
          error: {
            type: 'network',
            message: 'Unable to connect to backend'
          }
        }, '*');
      });
      
      await browser.pause(500);
      
      const errorBanner = await mainWindow.$('[data-testid="error-banner"]');
      if (await errorBanner.isDisplayed()) {
        await browser.checkElement(await errorBanner, 'network-error-banner');
      }
    });
    
    it('should match empty state views', async () => {
      // Clear all data
      await browser.execute(() => {
        window.postMessage({
          type: 'clear-data'
        }, '*');
      });
      
      await browser.pause(500);
      
      // Check empty states for different pages
      const pages = [
        { nav: 'nav-folders', name: 'folders-empty' },
        { nav: 'nav-shares', name: 'shares-empty' },
        { nav: 'nav-uploads', name: 'uploads-empty' },
        { nav: 'nav-downloads', name: 'downloads-empty' }
      ];
      
      for (const page of pages) {
        const navElement = await mainWindow.$(`[data-testid="${page.nav}"]`);
        await navElement.click();
        await browser.pause(500);
        
        await browser.checkScreen(`${page.name}-state`);
      }
    });
  });
  
  describe('Responsive Visual Tests', () => {
    it('should match tablet layout', async () => {
      await browser.setWindowSize(1024, 768);
      await browser.pause(500);
      
      await browser.checkScreen('tablet-dashboard');
      
      const folderNav = await mainWindow.$('[data-testid="nav-folders"]');
      await folderNav.click();
      await browser.pause(500);
      
      await browser.checkScreen('tablet-folders');
    });
    
    it('should match small screen layout', async () => {
      await browser.setWindowSize(800, 600);
      await browser.pause(500);
      
      await browser.checkScreen('small-dashboard');
      
      // Check if mobile menu is visible
      const mobileMenu = await mainWindow.$('[data-testid="mobile-menu"]');
      if (await mobileMenu.isDisplayed()) {
        await mobileMenu.click();
        await browser.pause(500);
        await browser.checkScreen('small-mobile-menu');
      }
    });
    
    after(async () => {
      // Restore window size
      await browser.maximizeWindow();
    });
  });
  
  describe('Theme Visual Tests', () => {
    it('should match light theme consistently', async () => {
      // Ensure light mode
      const body = await mainWindow.$('body');
      const className = await body.getAttribute('class');
      if (className && className.includes('dark')) {
        const darkModeToggle = await mainWindow.$('[data-testid="dark-mode-toggle"]');
        await darkModeToggle.click();
        await browser.pause(500);
      }
      
      await browser.checkScreen('theme-light-full');
    });
    
    it('should match dark theme consistently', async () => {
      const darkModeToggle = await mainWindow.$('[data-testid="dark-mode-toggle"]');
      await darkModeToggle.click();
      await browser.pause(500);
      
      await browser.checkScreen('theme-dark-full');
      
      // Check specific components in dark mode
      const components = [
        'dashboard',
        'nav-folders',
        'nav-shares',
        'nav-settings'
      ];
      
      for (const comp of components) {
        const navElement = await mainWindow.$(`[data-testid="${comp}"]`);
        if (await navElement.isDisplayed()) {
          await navElement.click();
          await browser.pause(500);
          await browser.checkScreen(`theme-dark-${comp}`);
        }
      }
    });
  });
});