import type { Options } from '@wdio/types';
import { spawn } from 'child_process';
import { join } from 'path';

let tauriDriver: any;

export const config: Options.Testrunner = {
  runner: 'local',
  
  specs: [
    './tests/e2e/**/*.spec.ts'
  ],
  
  maxInstances: 1,
  
  capabilities: [{
    browserName: 'chrome',  // Use chrome for CI testing
    'goog:chromeOptions': {
      args: process.env.CI ? ['--headless', '--disable-gpu'] : []
    }
  }],
  
  logLevel: 'info',
  bail: 0,
  baseUrl: 'http://localhost:1420',
  waitforTimeout: 10000,
  connectionRetryTimeout: 120000,
  connectionRetryCount: 3,
  
  services: process.env.CI ? [] : ['chromedriver'],
  
  framework: 'mocha',
  reporters: ['spec'],
  
  mochaOpts: {
    ui: 'bdd',
    timeout: 60000
  },
  
  // For CI, we'll use Chrome instead of Tauri for initial testing
  onPrepare: async function (config, capabilities) {
    if (!process.env.CI) {
      console.log('Starting tauri-driver...');
      const appPath = join(__dirname, 'src-tauri', 'target', 'release', 'usenet-sync-app');
      tauriDriver = spawn('tauri-driver', ['--port', '4444'], {
        stdio: 'inherit'
      });
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  },
  
  onComplete: async function() {
    if (tauriDriver) {
      console.log('Stopping tauri-driver...');
      tauriDriver.kill();
    }
  }
};