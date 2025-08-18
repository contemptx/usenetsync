# CRITICAL: NNTP Module Information

## DO NOT USE nntplib
- **nntplib is DISCONTINUED** as of Python 3.11
- It was removed from the Python standard library
- DO NOT attempt to use `import nntplib`

## USE pynntp Instead
- **Package name**: `pynntp`
- **Install command**: `pip install pynntp`
- **Import statement**: `from nntp import NNTPClient`

### Important Notes:
1. The package is called `pynntp` but you import it as `nntp` (NOT `pynntp`)
2. This is confusing but correct:
   - ✅ CORRECT: `from nntp import NNTPClient`
   - ❌ WRONG: `from pynntp import NNTPClient`
   - ❌ WRONG: `import nntplib`

### Example Usage:
```python
# Install: pip install pynntp
from nntp import NNTPClient

client = NNTPClient(
    host='news.example.com',
    port=563,
    username='user',
    password='pass',
    use_ssl=True
)
```

## Why This Matters
The UsenetSync application requires NNTP functionality to connect to Usenet servers. Without the correct module, the core functionality will not work.

## Requirements.txt Entry
```
pynntp>=1.0.2
```

---
**Remember**: Package is `pynntp`, import is `nntp`, NOT `nntplib`!