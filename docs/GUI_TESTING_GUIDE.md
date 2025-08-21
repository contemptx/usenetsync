# GUI Testing Guide for UsenetSync

## Overview

This guide covers the comprehensive GUI testing setup for the UsenetSync Tauri application, including:
- WebDriverIO with tauri-driver for automated testing
- Visual regression testing capabilities
- GitHub Actions CI/CD pipeline
- AI-powered test failure triage and autofix

## Architecture

```
┌─────────────────────────────────────────────┐
│           GitHub Actions Workflow           │
├─────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐      │
│  │ Windows Test │    │  Linux Test  │      │
│  └──────────────┘    └──────────────┘      │
│           │                  │              │
│           ▼                  ▼              │
│     ┌─────────────────────────────┐        │
│     │    WebDriverIO Runner        │        │
│     └─────────────────────────────┘        │
│                  │                          │
│                  ▼                          │
│     ┌─────────────────────────────┐        │
│     │     tauri-driver             │        │
│     └─────────────────────────────┘        │
│                  │                          │
│                  ▼                          │
│     ┌─────────────────────────────┐        │
│     │    Tauri Application         │        │
│     │    (React + Rust)            │        │
│     └─────────────────────────────┘        │
│                  │                          │
│                  ▼                          │
│     ┌─────────────────────────────┐        │
│     │    Test Results              │        │
│     │  - JUnit XML                 │        │
│     │  - Allure Reports            │        │
│     │  - Screenshots               │        │
│     └─────────────────────────────┘        │
│                  │                          │
│           Failure?                          │
│                  │                          │
│                  ▼                          │
│     ┌─────────────────────────────┐        │
│     │    AI Triage                 │        │
│     │  - Pattern Analysis          │        │
│     │  - Root Cause Detection      │        │
│     │  - Fix Suggestions           │        │
│     └─────────────────────────────┘        │
│                  │                          │
│                  ▼                          │
│     ┌─────────────────────────────┐        │
│     │    Autofix                   │        │
│     │  - Apply Suggestions         │        │
│     │  - Create PR                 │        │
│     └─────────────────────────────┘        │
└─────────────────────────────────────────────┘
```

## Setup Instructions

### Prerequisites

1. **Install Rust and Cargo**
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. **Install tauri-driver**
   ```bash
   cargo install tauri-driver
   ```

3. **Install Node.js dependencies**
   ```bash
   cd frontend
   npm install
   ```

4. **Install WebDriverIO packages**
   ```bash
   npm install --save-dev @wdio/cli @wdio/local-runner @wdio/mocha-framework
   npm install --save-dev @wdio/spec-reporter @wdio/allure-reporter @wdio/junit-reporter
   npm install --save-dev @wdio/globals ts-node webdriverio
   ```

### Configuration Files

#### 1. WebDriverIO Configuration (`frontend/wdio.conf.ts`)
- Configures test runner, capabilities, and reporters
- Sets up tauri-driver integration
- Defines test specs and timeout settings

#### 2. Test Specifications
- `frontend/tests/e2e/gui-complete-workflow.spec.ts` - Comprehensive workflow tests
- `frontend/tests/e2e/visual.spec.ts` - Visual regression tests
- `frontend/tests/e2e/basic-gui.spec.ts` - Basic functionality tests

#### 3. GitHub Actions Workflow (`.github/workflows/gui-tests.yml`)
- Runs tests on Windows and Linux
- Multiple Node.js versions
- AI triage on failures
- Automatic fix generation

## Running Tests

### Local Development

1. **Run all E2E tests**
   ```bash
   npm run test:e2e
   ```

2. **Run tests with visible browser**
   ```bash
   npm run test:e2e:headed
   ```

3. **Run specific test file**
   ```bash
   npx wdio run wdio.conf.ts --spec tests/e2e/basic-gui.spec.ts
   ```

4. **Debug mode**
   ```bash
   npm run test:e2e:debug
   ```

### CI/CD Pipeline

Tests run automatically on:
- Push to main, develop, or feature branches
- Pull requests
- Manual workflow dispatch

## Test Coverage

### 1. Application Launch
- Verifies app starts successfully
- Checks window title and initial state
- Validates main dashboard display

### 2. Folder Management
- Add folder functionality
- Folder indexing process
- Segmentation workflow
- Folder statistics display

### 3. Share Creation
- Public share creation
- Password-protected shares
- Private shares with user authorization
- Share link generation

### 4. Upload/Download
- Upload queue management
- Progress tracking
- Download from share ID
- Password-protected downloads
- Resume capability

### 5. Settings
- NNTP configuration
- Connection testing
- Dark mode toggle
- Security settings

### 6. Error Handling
- Network error recovery
- Invalid input validation
- Timeout handling
- Error notifications

### 7. Accessibility
- Keyboard navigation
- Screen reader support
- Focus management
- ARIA labels

### 8. Performance
- Load time metrics
- Large dataset handling
- Memory usage
- Scroll performance

### 9. Visual Regression
- Layout consistency
- Theme switching
- Responsive design
- Component styling

## AI-Powered Features

### Test Failure Triage

The AI triage system (`/.github/scripts/ai-triage.py`) analyzes:

1. **Failure Patterns**
   - Groups similar failures
   - Identifies systemic issues
   - Detects flaky tests

2. **Root Cause Analysis**
   - Timeout issues
   - Selector changes
   - API failures
   - Visual regressions

3. **Fix Suggestions**
   - Code changes
   - Configuration updates
   - Selector improvements
   - Timeout adjustments

### Automatic Fix Application

The autofix system (`.github/scripts/apply-autofix.js`) can:

1. **Apply Safe Fixes**
   - Update selectors
   - Increase timeouts
   - Fix configuration

2. **Create Pull Requests**
   - Automated PR creation
   - Detailed change summary
   - Test results included

3. **Verification**
   - Re-run tests after fixes
   - Validate changes
   - Report success rate

## Best Practices

### 1. Test Structure
```typescript
describe('Feature Area', () => {
  before(async () => {
    // Setup
  });
  
  it('should perform specific action', async () => {
    // Arrange
    const element = await $('[data-testid="element"]');
    
    // Act
    await element.click();
    
    // Assert
    await expect(element).toHaveText('Expected');
  });
  
  after(async () => {
    // Cleanup
  });
});
```

### 2. Selectors
- Use `data-testid` attributes for stability
- Avoid CSS classes that might change
- Use semantic HTML where possible

### 3. Waits and Timeouts
```typescript
// Good - Explicit wait
await browser.waitUntil(
  async () => await element.isDisplayed(),
  { timeout: 10000, timeoutMsg: 'Element not visible' }
);

// Bad - Fixed pause
await browser.pause(5000);
```

### 4. Screenshots
- Take screenshots on failures
- Name descriptively
- Store in organized folders

### 5. Test Data
- Use test-specific data
- Clean up after tests
- Avoid production data

## Troubleshooting

### Common Issues

1. **tauri-driver not found**
   ```bash
   cargo install tauri-driver
   export PATH="$HOME/.cargo/bin:$PATH"
   ```

2. **Application doesn't launch**
   - Ensure app is built: `npm run build:tauri`
   - Check tauri-driver is running
   - Verify path in wdio.conf.ts

3. **Tests timeout**
   - Increase `waitforTimeout` in config
   - Add explicit waits
   - Check backend is running

4. **Visual regression failures**
   - Update baselines if changes are intentional
   - Check for OS-specific rendering
   - Adjust mismatch tolerance

### Debug Techniques

1. **Enable debug logging**
   ```bash
   DEBUG=* npm run test:e2e
   ```

2. **Run in headed mode**
   ```bash
   npm run test:e2e:headed
   ```

3. **Use browser.debug()**
   ```typescript
   it('debug test', async () => {
     await browser.debug(); // Pauses execution
   });
   ```

4. **Check screenshots**
   - Located in `test-screenshots/`
   - Named by test and timestamp

## Reporting

### Test Reports

1. **Allure Reports**
   - Interactive HTML reports
   - Test history tracking
   - Failure analysis
   - Screenshots attached

2. **JUnit XML**
   - CI/CD integration
   - Test metrics
   - Failure details

3. **Console Output**
   - Real-time progress
   - Error messages
   - Debug information

### Metrics Tracked

- Test execution time
- Pass/fail rate
- Flaky test detection
- Coverage percentage
- Performance metrics

## Integration with Development

### Pre-commit Hooks
```json
{
  "husky": {
    "hooks": {
      "pre-commit": "npm run test:e2e -- --spec tests/e2e/basic-gui.spec.ts"
    }
  }
}
```

### Pull Request Checks
- Automated test runs
- Required passing tests
- Visual regression approval
- Performance benchmarks

## Future Enhancements

1. **Accessibility Testing**
   - WCAG compliance checks
   - Screen reader testing
   - Keyboard navigation validation

2. **Performance Testing**
   - Load testing
   - Memory profiling
   - Render performance

3. **Security Testing**
   - Input validation
   - XSS prevention
   - Authentication flows

4. **Cross-platform Testing**
   - macOS support
   - Different Linux distributions
   - ARM architecture

## Resources

- [WebDriverIO Documentation](https://webdriver.io/)
- [Tauri Testing Guide](https://tauri.app/v1/guides/testing/)
- [Allure Reports](https://docs.qameta.io/allure/)
- [GitHub Actions](https://docs.github.com/en/actions)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review test logs in GitHub Actions
3. Open an issue with test artifacts attached