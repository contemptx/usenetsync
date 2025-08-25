# Pull Request Checklist

## Description
Brief description of changes:

## Pre-Merge Checklist

### ❌ No Placeholders
- [ ] No "test", "demo", "sample" strings in code
- [ ] No "TODO" or "FIXME" comments
- [ ] No hardcoded test paths ("/tmp/test", "C:\temp\test")
- [ ] No example.com email addresses
- [ ] No placeholder IDs (TEST-123, DEMO-456)

### ✅ Real Systems
- [ ] Uses real NNTP server configuration (news.newshosting.com)
- [ ] Connects to real database (no in-memory)
- [ ] No random data generation (random.uniform, random.randint)
- [ ] No Mock/Fake/Stub classes
- [ ] All metrics are measured, not simulated

### 🔐 Usenet Compliance
- [ ] No email fields in API endpoints
- [ ] No permission levels (read/write/admin)
- [ ] Client-generated Message-IDs only
- [ ] Append-only operations (no edit/delete)
- [ ] Binary access model (encrypted or not)

### 🧪 Testing
- [ ] Tested with real Usenet server
- [ ] Verified with real database
- [ ] No mock objects in tests
- [ ] All operations are idempotent
- [ ] Proper error handling (no generic messages)

### 📝 Documentation
- [ ] No example code with placeholders
- [ ] Real configuration examples provided
- [ ] Actual error messages documented
- [ ] Real Message-ID format shown

## Automated Checks
- [ ] Pre-commit hook passed
- [ ] CI/CD validation passed
- [ ] Enforcement module validated
- [ ] No violations found

## Manual Verification
Run these commands before submitting:
```bash
# Check for banned patterns
grep -r "test@example.com" backend/src
grep -r "/tmp/test" backend/src
grep -r "TODO\|FIXME" backend/src

# Validate enforcement
python backend/src/unified/enforcement.py

# Run validators on changed files
python backend/src/unified/validators.py [changed_files]
```

## Reviewer Notes
- Check for subtle placeholders (example.org, foo.bar, etc.)
- Verify NNTP operations are one-way
- Ensure no PII is stored or transmitted
- Confirm binary access model is maintained

---
By submitting this PR, I confirm that:
1. All code uses real systems, not mocks
2. No placeholder data exists
3. Usenet principles are followed
4. Privacy is maintained (no emails)
5. Access is binary (no permissions)