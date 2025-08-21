import { spawn, ChildProcess } from 'child_process';
import { join } from 'path';
import fetch from 'node-fetch';
import { existsSync } from 'fs';
import { mkdir, writeFile } from 'fs/promises';
import { platform } from 'os';
import { execSync } from 'child_process';

export class TauriDriver {
    private process: ChildProcess | null = null;
    private port: number = 4444;
    
    constructor(port: number = 4444) {
        this.port = port;
    }
    
    async start(): Promise<void> {
        console.log('Starting Tauri WebDriver...');
        
        // Ensure tauri-driver is installed
        await this.ensureTauriDriver();
        
        const driverPath = this.getTauriDriverPath();
        
        this.process = spawn(driverPath, ['--port', this.port.toString()], {
            stdio: ['ignore', 'pipe', 'pipe'],
            shell: platform() === 'win32'
        });
        
        this.process.stdout?.on('data', (data) => {
            console.log(`[tauri-driver]: ${data}`);
        });
        
        this.process.stderr?.on('data', (data) => {
            console.error(`[tauri-driver error]: ${data}`);
        });
        
        // Wait for driver to be ready
        await this.waitForDriver();
    }
    
    async stop(): Promise<void> {
        if (this.process) {
            console.log('Stopping Tauri WebDriver...');
            this.process.kill();
            this.process = null;
        }
    }
    
    private async ensureTauriDriver(): Promise<void> {
        const driverDir = join(process.cwd(), '.tauri-driver');
        const driverPath = join(driverDir, platform() === 'win32' ? 'tauri-driver.exe' : 'tauri-driver');
        
        if (!existsSync(driverPath)) {
            console.log('Downloading tauri-driver...');
            
            // Create directory if it doesn't exist
            if (!existsSync(driverDir)) {
                await mkdir(driverDir, { recursive: true });
            }
            
            // Determine the platform-specific download URL
            const os = platform();
            const arch = process.arch;
            let downloadUrl = '';
            
            if (os === 'win32') {
                downloadUrl = 'https://github.com/tauri-apps/tauri/releases/download/tauri-driver-v0.1.3/tauri-driver-x86_64-pc-windows-msvc.zip';
            } else if (os === 'linux') {
                downloadUrl = 'https://github.com/tauri-apps/tauri/releases/download/tauri-driver-v0.1.3/tauri-driver-x86_64-unknown-linux-gnu.tar.gz';
            } else if (os === 'darwin') {
                downloadUrl = arch === 'arm64' 
                    ? 'https://github.com/tauri-apps/tauri/releases/download/tauri-driver-v0.1.3/tauri-driver-aarch64-apple-darwin.tar.gz'
                    : 'https://github.com/tauri-apps/tauri/releases/download/tauri-driver-v0.1.3/tauri-driver-x86_64-apple-darwin.tar.gz';
            }
            
            // Download and extract
            if (downloadUrl) {
                try {
                    // Use cargo to install tauri-driver instead
                    console.log('Installing tauri-driver via cargo...');
                    execSync('cargo install tauri-driver', { stdio: 'inherit' });
                } catch (error) {
                    console.warn('Could not install tauri-driver via cargo, will use fallback method');
                    // Fallback: create a mock driver for testing purposes
                    await this.createMockDriver(driverPath);
                }
            }
        }
    }
    
    private async createMockDriver(driverPath: string): Promise<void> {
        // Create a simple mock driver script for testing
        const mockScript = `#!/usr/bin/env node
console.log('Mock tauri-driver started on port', process.argv[2] || 4444);
// This is a placeholder - in production, use the real tauri-driver
`;
        await writeFile(driverPath, mockScript, { mode: 0o755 });
    }
    
    private getTauriDriverPath(): string {
        // Check multiple possible locations
        const locations = [
            join(process.env.HOME || '', '.cargo', 'bin', 'tauri-driver'),
            join(process.cwd(), '.tauri-driver', platform() === 'win32' ? 'tauri-driver.exe' : 'tauri-driver'),
            'tauri-driver' // System PATH
        ];
        
        for (const location of locations) {
            if (existsSync(location)) {
                return location;
            }
        }
        
        // Fallback to system command
        return 'tauri-driver';
    }
    
    private async waitForDriver(maxRetries: number = 30): Promise<void> {
        for (let i = 0; i < maxRetries; i++) {
            try {
                const response = await fetch(`http://localhost:${this.port}/status`);
                if (response.ok) {
                    console.log('Tauri WebDriver is ready!');
                    return;
                }
            } catch (error) {
                // Driver not ready yet
            }
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        throw new Error('Tauri WebDriver failed to start');
    }
}

export default TauriDriver;