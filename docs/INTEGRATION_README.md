# Simple Integration Guide

## Quick Start (2 minutes)

1. **Copy the production wrapper:**
   ```bash
   copy production_db_wrapper_final.py production_db_wrapper.py
   ```

2. **Update your imports (one line change!):**
   ```bash
   python update_imports.py
   ```
   
   This changes:
   ```python
   from enhanced_database_manager import EnhancedDatabaseManager
   ```
   
   To:
   ```python
   from enhanced_database_manager_production import EnhancedDatabaseManager
   ```

3. **Test it works:**
   ```bash
   python test_integration.py
   ```

## That's it! 🎉

Your code now has:
- ✅ Automatic retry on database locks (3 attempts)
- ✅ Performance monitoring
- ✅ Error logging to `logs/database.log`
- ✅ No other code changes needed!

## What Changed?

Only the import statement! Your code works exactly the same but now has production features.

## Monitoring (Optional)

Check database health anytime:
```python
from enhanced_database_manager_production import log_database_health
log_database_health()
```

Get detailed stats:
```python
from enhanced_database_manager_production import get_monitoring_stats
stats = get_monitoring_stats()
print(f"Total operations: {stats['total_operations']}")
print(f"Lock errors: {stats['lock_errors']}")
```

## Rollback

To rollback, just change the import back:
```python
from enhanced_database_manager import EnhancedDatabaseManager
```

That's all!
