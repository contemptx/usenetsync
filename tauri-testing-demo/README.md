# Tauri App GUI Testing Framework

A comprehensive testing solution for Tauri applications featuring WebDriverIO integration, visual regression testing, AI-powered test triage, and cross-platform CI/CD support.

## 🚀 Features

### ✅ Complete E2E Testing
- **WebDriverIO Integration**: Full browser automation support for Tauri apps
- **Tauri-Driver Support**: Native Tauri window control and interaction
- **React Component Testing**: Interact with React components directly
- **Cross-platform**: Works on Windows, Linux, and macOS

### 📸 Visual Regression Testing
- **Pixel-perfect comparisons**: Detect visual changes automatically
- **Responsive testing**: Test across different window sizes
- **Component screenshots**: Capture specific UI elements
- **Baseline management**: Easy update and maintenance of visual baselines

### 🤖 AI-Powered Test Intelligence
- **Automatic failure analysis**: AI categorizes and analyzes test failures
- **Smart fix suggestions**: Get specific recommendations for fixing failures
- **Auto-fix capability**: Apply safe fixes automatically
- **Pattern recognition**: Learn from historical test data

### 🔄 GitHub Actions CI/CD
- **Multi-platform testing**: Run tests on Windows and Linux simultaneously
- **Parallel execution**: Test across multiple Node.js versions
- **Artifact management**: Automatic storage of test results and screenshots
- **PR integration**: Automatic comments with test results on pull requests

## 📦 Installation

```bash
# Clone the repository
git clone <your-repo>
cd tauri-testing-demo

# Install dependencies
npm install

# Install Rust and Tauri prerequisites
# Linux:
sudo apt-get update && sudo apt-get install -y \
  libwebkit2gtk-4.0-dev \
  libgtk-3-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev

# Windows:
# Install Visual Studio 2022 with C++ workload

# Install tauri-driver
cargo install tauri-driver
```

## 🎯 Usage

### Running Tests Locally

```bash
# Run all E2E tests
npm run test:e2e

# Run visual regression tests only
npm run test:visual

# Run app interaction tests only
npm run test:app

# Debug mode with verbose logging
npm run test:debug

# Update visual baselines
npm run visual:update
```

### Test Reports

```bash
# Generate Allure report
npm run allure:generate

# Open Allure report in browser
npm run allure:open
```

### AI-Powered Test Analysis

```bash
# Run AI triage on test failures
npm run ai:triage

# Apply automatic fixes (if available)
npm run ai:autofix
```

## 🧪 Test Structure

```
test/
├── specs/
│   ├── app.test.ts         # Application functionality tests
│   └── visual.test.ts      # Visual regression tests
├── helpers/
│   └── tauri-driver.ts     # Tauri WebDriver helper
└── visual/
    ├── baseline/           # Visual regression baselines
    ├── screenshots/        # Test screenshots
    └── diff/              # Visual differences
```

## 📝 Writing Tests

### Basic E2E Test

```typescript
import { expect } from '@wdio/globals';
import { browser } from '@wdio/globals';

describe('My Tauri App', () => {
    it('should interact with buttons', async () => {
        const button = await browser.$('button');
        await button.click();
        
        const result = await browser.$('.result');
        await expect(result).toHaveText('Clicked!');
    });
});
```

### Visual Regression Test

```typescript
describe('Visual Tests', () => {
    it('should match the homepage', async () => {
        const result = await browser.checkFullPageScreen('homepage', {
            hideScrollBars: true,
            disableCSSAnimation: true
        });
        
        expect(result).toBeLessThanOrEqual(5); // 5% threshold
    });
});
```

## 🔧 Configuration

### WebDriverIO Configuration (`wdio.conf.ts`)

Key configuration options:

```typescript
export const config = {
    specs: ['./test/specs/**/*.ts'],
    capabilities: [{
        browserName: 'tauri',
        'tauri:options': {
            application: '../src-tauri/target/release/app-name',
        }
    }],
    services: [
        ['visual', {
            baselineFolder: './test/visual/baseline',
            formatImageName: '{tag}-{browserName}-{width}x{height}',
        }]
    ],
    reporters: ['spec', 'allure']
};
```

## 🚀 CI/CD with GitHub Actions

The project includes a comprehensive GitHub Actions workflow that:

1. **Multi-platform Testing**: Runs on Ubuntu and Windows
2. **Visual Regression Checks**: Compares screenshots across builds
3. **AI Analysis**: Analyzes failures and suggests fixes
4. **Auto-fix**: Can automatically apply safe fixes
5. **Report Deployment**: Publishes test reports to GitHub Pages

### Setting up GitHub Actions

1. Add the following secrets to your repository:
   - `OPENAI_API_KEY`: For AI-powered analysis (optional)
   - `TAURI_PRIVATE_KEY`: For app signing (optional)
   - `TAURI_KEY_PASSWORD`: For app signing (optional)

2. Push to main or create a PR to trigger the workflow

## 🤖 AI-Powered Features

### Test Failure Analysis

The AI system analyzes test failures and categorizes them:
- **Timeout errors**: Suggests increasing wait times
- **Element not found**: Recommends selector updates
- **Visual differences**: Proposes threshold adjustments
- **Network issues**: Suggests retry strategies

### Automatic Fixes

Safe fixes that can be applied automatically:
- Timeout value increases
- Visual threshold adjustments
- Retry count modifications
- Wait condition additions

### Manual Review Required

Some fixes require human review:
- Selector changes
- Business logic updates
- New feature implementations

## 📊 Test Reports

### Allure Reports
- Detailed test execution timeline
- Step-by-step test breakdown
- Screenshot attachments
- Failure categorization
- Historical trends

### Visual Diff Reports
- Side-by-side comparisons
- Highlighted differences
- Percentage change metrics
- Component-level analysis

## 🎨 Best Practices

### 1. Use Data Test IDs
```tsx
<button data-testid="submit-button">Submit</button>
```

### 2. Wait for Elements
```typescript
await browser.waitUntil(
    async () => await element.isDisplayed(),
    { timeout: 5000 }
);
```

### 3. Handle Dynamic Content
```typescript
const result = await browser.checkElement(element, 'component', {
    hideElements: ['.timestamp', '.random-id']
});
```

### 4. Organize Tests Logically
- Group related tests in describe blocks
- Use meaningful test names
- Keep tests independent
- Clean up after tests

## 🐛 Troubleshooting

### Common Issues

1. **Tauri-driver not found**
   ```bash
   cargo install tauri-driver
   ```

2. **Visual tests failing**
   ```bash
   npm run visual:update  # Update baselines
   ```

3. **Timeout errors**
   - Increase `waitforTimeout` in `wdio.conf.ts`
   - Add explicit waits in tests

4. **CI failures**
   - Check GitHub Actions logs
   - Review AI triage suggestions
   - Verify environment variables

## 📚 Resources

- [WebDriverIO Documentation](https://webdriver.io/)
- [Tauri Testing Guide](https://tauri.app/guides/testing/)
- [Visual Testing Best Practices](https://webdriver.io/docs/visual-testing/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Tauri team for the excellent framework
- WebDriverIO community for the testing tools
- OpenAI for AI-powered analysis capabilities

---

**Happy Testing! 🎉**
