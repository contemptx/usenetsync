import type { Options } from '@wdio/types';
import { spawn, ChildProcess } from 'child_process';
import { join } from 'path';
import { existsSync } from 'fs';
import TauriDriver from './test/helpers/tauri-driver';

// Store the tauri-driver process
let tauriDriver: TauriDriver;

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
        './test/specs/**/*.ts'
    ],
    exclude: [],
    
    //
    // ============
    // Capabilities
    // ============
    maxInstances: 1,
    capabilities: [{
        browserName: 'tauri',
        'tauri:options': {
            application: '../src-tauri/target/release/tauri-testing-demo',
        },
        'wdio:devtoolsOptions': {
            backend: 'webdriver',
        },
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
    
    //
    // Test runner services
    services: [
        ['visual', {
            baselineFolder: join(process.cwd(), 'test', 'visual', 'baseline'),
            formatImageName: '{tag}-{browserName}-{width}x{height}',
            screenshotPath: join(process.cwd(), 'test', 'visual', 'screenshots'),
            savePerInstance: true,
            autoSaveBaseline: true,
            blockOutStatusBar: true,
            blockOutToolBar: true,
            clearRuntimeFolder: true,
        }]
    ],
    
    framework: 'mocha',
    reporters: [
        'spec',
        ['allure', {
            outputDir: 'allure-results',
            disableWebdriverStepsReporting: false,
            disableWebdriverScreenshotsReporting: false,
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
    onPrepare: async function (config, capabilities) {
        console.log('Starting tauri-driver...');
        
        // Check if we're in CI environment
        const isCI = process.env.CI === 'true';
        
        // Build the app if needed
        if (!existsSync(join(process.cwd(), 'src-tauri', 'target', 'release', 'tauri-testing-demo'))) {
            console.log('Building Tauri app...');
            const buildProcess = spawn('npm', ['run', 'tauri', 'build'], {
                cwd: process.cwd(),
                shell: true,
                stdio: 'inherit'
            });
            
            await new Promise((resolve, reject) => {
                buildProcess.on('close', (code) => {
                    if (code === 0) {
                        resolve(undefined);
                    } else {
                        reject(new Error(`Build failed with code ${code}`));
                    }
                });
            });
        }
        
        // Start tauri-driver using our custom helper
        tauriDriver = new TauriDriver(4444);
        await tauriDriver.start();
    },
    
    onComplete: async function() {
        console.log('Stopping tauri-driver...');
        if (tauriDriver) {
            await tauriDriver.stop();
        }
    },
    
    afterTest: async function(test, context, { error, result, duration, passed, retries }) {
        if (!passed) {
            await browser.takeScreenshot();
        }
    },
}