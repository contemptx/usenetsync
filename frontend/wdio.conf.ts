import type { Options } from '@wdio/types';
import { spawn, spawnSync } from 'child_process';
import { join } from 'path';

// Keep track of the tauri-driver process
let tauriDriver: any;

export const config: Options.Testrunner = {
  //
  // ====================
  // Runner Configuration
  // ====================
  runner: 'local',
  
  //
  // ==================
  // Specify Test Files
  // ==================
  specs: [
    './tests/e2e/**/*.spec.ts'
  ],
  exclude: [],
  
  //
  // ============
  // Capabilities
  // ============
  maxInstances: 1,
  capabilities: [{
    maxInstances: 1,
    'tauri:options': {
      application: '../src-tauri/target/release/usenet-sync-app',
    },
    'wdio:webdriverOptions': {
      capabilities: {
        browserName: 'wry',
        browserVersion: '',
        platformName: process.platform === 'win32' ? 'windows' : 'linux'
      }
    }
  }],
  
  //
  // ===================
  // Test Configurations
  // ===================
  logLevel: 'info',
  bail: 0,
  baseUrl: 'http://localhost',
  waitforTimeout: 10000,
  connectionRetryTimeout: 120000,
  connectionRetryCount: 3,
  
  services: [],
  
  framework: 'mocha',
  reporters: [
    'spec',
    ['allure', {
      outputDir: 'allure-results',
      disableWebdriverStepsReporting: false,
      disableWebdriverScreenshotsReporting: false,
    }],
    ['junit', {
      outputDir: './test-results',
      outputFileFormat: function(options: any) {
        return `results-${options.cid}.${options.capabilities.platformName}.xml`;
      }
    }]
  ],
  
  mochaOpts: {
    ui: 'bdd',
    timeout: 60000
  },
  
  //
  // =====
  // Hooks
  // =====
  onPrepare: function (config, capabilities) {
    // Start tauri-driver
    const tauriDriverPath = process.platform === 'win32' 
      ? 'tauri-driver.exe' 
      : 'tauri-driver';
    
    console.log('Starting tauri-driver...');
    tauriDriver = spawn(tauriDriverPath, [], {
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    
    tauriDriver.stdout.on('data', (data: Buffer) => {
      console.log(`tauri-driver: ${data.toString()}`);
    });
    
    tauriDriver.stderr.on('data', (data: Buffer) => {
      console.error(`tauri-driver error: ${data.toString()}`);
    });
    
    // Wait for driver to be ready
    return new Promise((resolve) => setTimeout(resolve, 5000));
  },
  
  onComplete: function() {
    // Kill the tauri-driver process
    if (tauriDriver) {
      console.log('Stopping tauri-driver...');
      tauriDriver.kill();
    }
  },
  
  beforeSession: function (config, capabilities, specs) {
    // Build the Tauri app if needed
    const buildResult = spawnSync('npm', ['run', 'build'], {
      cwd: join(__dirname),
      shell: true,
      stdio: 'inherit'
    });
    
    if (buildResult.status !== 0) {
      throw new Error('Failed to build Tauri app');
    }
  },
  
  before: function (capabilities, specs) {
    // Set up TypeScript support
    require('ts-node').register({
      transpileOnly: true,
      project: './tsconfig.json'
    });
  },
  
  afterTest: async function(test, context, { error, result, duration, passed, retries }) {
    if (!passed) {
      // Take screenshot on failure
      await browser.takeScreenshot();
    }
  }
};