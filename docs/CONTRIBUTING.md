# Contributing to UsenetSync

Thank you for your interest in contributing to UsenetSync! This document provides guidelines and instructions for contributing.

## 🤝 Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## 🚀 Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/usenetsync.git
   cd usenetsync
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/contemptx/usenetsync.git
   ```

## 🔧 Development Setup

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## 📝 Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Your Changes

- Follow existing code style
- Add tests for new functionality
- Update documentation as needed
- Use meaningful commit messages

### 3. Commit Guidelines

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `test:` Adding tests
- `chore:` Maintenance tasks

Example:
```bash
git commit -m "feat: add multi-threaded upload support"
```

### 4. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=usenet_sync

# Run specific test
pytest tests/test_upload_system.py
```

### 5. Push Changes

```bash
git push origin feature/your-feature-name
```

### 6. Create Pull Request

1. Go to your fork on GitHub
2. Click "Pull Request"
3. Fill out the PR template
4. Link any related issues

## 🧪 Testing

- Write tests for new features
- Ensure all tests pass
- Maintain or improve code coverage
- Test on Windows and Linux if possible

## 📚 Documentation

- Update docstrings for new functions
- Update README if needed
- Add examples for new features
- Update API documentation

## 🐛 Reporting Issues

1. Search existing issues first
2. Use issue templates
3. Provide detailed information:
   - OS and Python version
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs

## 💡 Suggesting Features

1. Check if already suggested
2. Open a discussion first for major features
3. Use feature request template
4. Explain use case clearly

## 🔍 Code Review Process

1. Automated checks must pass
2. At least one maintainer review
3. Address all feedback
4. Keep PR focused and small

## 📋 Checklist

Before submitting a PR:

- [ ] Tests pass locally
- [ ] Code follows project style
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] PR description is clear
- [ ] Related issues are linked

## 🎯 Areas for Contribution

- 🐛 Bug fixes
- ✨ New features
- 📚 Documentation improvements
- 🧪 Test coverage
- ⚡ Performance optimizations
- 🌐 Internationalization
- 🎨 UI/UX improvements

## 🙏 Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing to UsenetSync! 🚀
