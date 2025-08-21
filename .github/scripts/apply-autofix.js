#!/usr/bin/env node
/**
 * Apply AI-suggested fixes automatically
 */

const fs = require('fs');
const path = require('path');

class AutoFixer {
  constructor() {
    this.triageResults = this.loadTriageResults();
    this.changedFiles = [];
    this.appliedFixes = [];
  }

  loadTriageResults() {
    try {
      const resultsPath = path.join('triage-results', 'triage-results.json');
      return JSON.parse(fs.readFileSync(resultsPath, 'utf8'));
    } catch (error) {
      console.error('Failed to load triage results:', error);
      return { suggestions: [] };
    }
  }

  applyFixes() {
    console.log('Applying AI-suggested fixes...\n');
    
    for (const suggestion of this.triageResults.suggestions) {
      if (suggestion.review_needed) {
        console.log(`⚠️  Skipping fix requiring review: ${suggestion.type}`);
        continue;
      }

      switch (suggestion.type) {
        case 'selector':
          this.fixSelector(suggestion);
          break;
        case 'timeout':
          this.fixTimeout(suggestion);
          break;
        case 'config':
          this.fixConfig(suggestion);
          break;
        case 'visual':
          this.fixVisual(suggestion);
          break;
        default:
          console.log(`Unknown fix type: ${suggestion.type}`);
      }
    }

    this.saveChanges();
  }

  fixSelector(suggestion) {
    console.log(`Fixing selector in test: ${suggestion.test}`);
    
    // Find test file
    const testFiles = this.findTestFiles(suggestion.test);
    
    for (const testFile of testFiles) {
      let content = fs.readFileSync(testFile, 'utf8');
      const originalContent = content;
      
      // Apply selector fixes
      if (suggestion.code) {
        // Find the test case
        const testRegex = new RegExp(`it\\(['"\`]${suggestion.test}['"\`].*?\\{([\\s\\S]*?)\\}\\);`, 'g');
        content = content.replace(testRegex, (match, testBody) => {
          // Add wait before element interaction
          const improvedBody = testBody.replace(
            /const (\w+) = await mainWindow\.\$\('([^']+)'\);/g,
            `const $1 = await mainWindow.$('$2');\n    await browser.waitUntil(async () => await $1.isDisplayed(), { timeout: 10000 });`
          );
          return match.replace(testBody, improvedBody);
        });
      }
      
      if (content !== originalContent) {
        fs.writeFileSync(testFile, content);
        this.changedFiles.push(testFile);
        this.appliedFixes.push({
          type: 'selector',
          file: testFile,
          test: suggestion.test
        });
        console.log(`✅ Fixed selector in ${testFile}`);
      }
    }
  }

  fixTimeout(suggestion) {
    console.log(`Fixing timeout in test: ${suggestion.test}`);
    
    const testFiles = this.findTestFiles(suggestion.test);
    
    for (const testFile of testFiles) {
      let content = fs.readFileSync(testFile, 'utf8');
      const originalContent = content;
      
      // Increase timeouts
      content = content.replace(
        /timeout:\s*\d+/g,
        'timeout: 30000'
      );
      
      // Add timeout to waitUntil calls
      content = content.replace(
        /browser\.waitUntil\(([^)]+)\)/g,
        'browser.waitUntil($1, { timeout: 30000 })'
      );
      
      if (content !== originalContent) {
        fs.writeFileSync(testFile, content);
        this.changedFiles.push(testFile);
        this.appliedFixes.push({
          type: 'timeout',
          file: testFile,
          test: suggestion.test
        });
        console.log(`✅ Fixed timeouts in ${testFile}`);
      }
    }
  }

  fixConfig(suggestion) {
    console.log(`Fixing configuration: ${suggestion.file}`);
    
    const configPath = path.join('frontend', suggestion.file);
    
    if (fs.existsSync(configPath)) {
      let content = fs.readFileSync(configPath, 'utf8');
      const originalContent = content;
      
      if (suggestion.change.includes('waitforTimeout')) {
        content = content.replace(
          /waitforTimeout:\s*\d+/,
          'waitforTimeout: 30000'
        );
      }
      
      if (suggestion.change.includes('connectionRetryTimeout')) {
        content = content.replace(
          /connectionRetryTimeout:\s*\d+/,
          'connectionRetryTimeout: 180000'
        );
      }
      
      if (content !== originalContent) {
        fs.writeFileSync(configPath, content);
        this.changedFiles.push(configPath);
        this.appliedFixes.push({
          type: 'config',
          file: configPath,
          change: suggestion.change
        });
        console.log(`✅ Fixed configuration in ${configPath}`);
      }
    }
  }

  fixVisual(suggestion) {
    console.log(`Applying visual fixes from: ${suggestion.screenshot}`);
    
    for (const fix of suggestion.fixes || []) {
      if (fix.includes('CSS') || fix.includes('style')) {
        this.fixCSS(fix);
      } else if (fix.includes('component') || fix.includes('import')) {
        this.fixComponent(fix);
      }
    }
  }

  fixCSS(fix) {
    // Find and fix CSS issues
    const cssFiles = this.findFiles('frontend/src', '.css', '.scss');
    
    for (const cssFile of cssFiles) {
      let content = fs.readFileSync(cssFile, 'utf8');
      const originalContent = content;
      
      // Common CSS fixes
      if (fix.includes('flexbox')) {
        content = content.replace(
          /\.stats-container\s*{/g,
          '.stats-container {\n  display: flex;\n  flex-wrap: wrap;'
        );
      }
      
      if (fix.includes('alignment')) {
        content = content.replace(
          /align-items:\s*\w+;/g,
          'align-items: center;'
        );
      }
      
      if (content !== originalContent) {
        fs.writeFileSync(cssFile, content);
        this.changedFiles.push(cssFile);
        this.appliedFixes.push({
          type: 'css',
          file: cssFile,
          fix: fix
        });
        console.log(`✅ Fixed CSS in ${cssFile}`);
      }
    }
  }

  fixComponent(fix) {
    // Find and fix component issues
    const componentFiles = this.findFiles('frontend/src', '.tsx', '.jsx');
    
    for (const componentFile of componentFiles) {
      let content = fs.readFileSync(componentFile, 'utf8');
      const originalContent = content;
      
      // Add missing imports
      if (fix.includes('DarkModeToggle') && !content.includes('DarkModeToggle')) {
        content = `import { DarkModeToggle } from './components/DarkModeToggle';\n${content}`;
      }
      
      if (content !== originalContent) {
        fs.writeFileSync(componentFile, content);
        this.changedFiles.push(componentFile);
        this.appliedFixes.push({
          type: 'component',
          file: componentFile,
          fix: fix
        });
        console.log(`✅ Fixed component in ${componentFile}`);
      }
    }
  }

  findTestFiles(testName) {
    const testDir = path.join('frontend', 'tests', 'e2e');
    const files = [];
    
    if (fs.existsSync(testDir)) {
      const allFiles = fs.readdirSync(testDir);
      for (const file of allFiles) {
        if (file.endsWith('.spec.ts') || file.endsWith('.spec.js')) {
          const filePath = path.join(testDir, file);
          const content = fs.readFileSync(filePath, 'utf8');
          if (content.includes(testName)) {
            files.push(filePath);
          }
        }
      }
    }
    
    return files;
  }

  findFiles(dir, ...extensions) {
    const files = [];
    
    function walk(currentDir) {
      if (!fs.existsSync(currentDir)) return;
      
      const items = fs.readdirSync(currentDir);
      for (const item of items) {
        const fullPath = path.join(currentDir, item);
        const stat = fs.statSync(fullPath);
        
        if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
          walk(fullPath);
        } else if (stat.isFile()) {
          if (extensions.some(ext => item.endsWith(ext))) {
            files.push(fullPath);
          }
        }
      }
    }
    
    walk(dir);
    return files;
  }

  saveChanges() {
    console.log('\n📝 Summary of changes:');
    console.log(`- Files modified: ${this.changedFiles.length}`);
    console.log(`- Fixes applied: ${this.appliedFixes.length}`);
    
    // Save summary for GitHub Actions
    const summary = {
      changedFiles: this.changedFiles,
      appliedFixes: this.appliedFixes,
      timestamp: new Date().toISOString()
    };
    
    fs.writeFileSync('autofix-summary.json', JSON.stringify(summary, null, 2));
    
    // Set GitHub Actions outputs
    if (this.changedFiles.length > 0) {
      console.log('::set-output name=changes::true');
      
      const changesSummary = this.appliedFixes.map(fix => 
        `- ${fix.type}: ${path.basename(fix.file)}${fix.test ? ` (${fix.test})` : ''}`
      ).join('\n');
      
      console.log(`::set-output name=changes-summary::${changesSummary}`);
    }
  }
}

// Main execution
const fixer = new AutoFixer();
fixer.applyFixes();