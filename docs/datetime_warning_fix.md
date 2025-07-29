# Fixing SQLite DateTime Warning

The warning about datetime adapter can be fixed by adding this to enhanced_database_manager.py:

```python
import sqlite3
from datetime import datetime

# Register datetime adapter for SQLite
def adapt_datetime(ts):
    return ts.isoformat()

def convert_datetime(ts):
    return datetime.fromisoformat(ts.decode())

# Register the adapter and converter
sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("timestamp", convert_datetime)
```

Add this at the top of the EnhancedDatabaseManager class or in the module initialization.

Alternatively, you can use datetime.isoformat() when storing and datetime.fromisoformat() when retrieving.
