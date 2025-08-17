# TurboActivate Licensing System

## Overview
This directory contains the TurboActivate licensing integration for UsenetSync.

**Version GUID**: `lzyz4mi2lgoawqj5bkjjvjceygsqfdi`

## Directory Structure
```
licensing/
├── turboactivate_integration.py  # Main Python integration
├── data/
│   └── TurboActivate.dat         # Product configuration (DO NOT MODIFY)
└── README.md                     # This file
```

## Required Libraries

Download the following libraries from your LimeLM account and place them in `/workspace/libs/`:

### Windows
- `libs/windows/TurboActivate.dll` (32-bit)
- `libs/windows/TurboActivate64.dll` (64-bit)

### macOS
- `libs/macos/libTurboActivate.dylib`

### Linux
- `libs/linux/libTurboActivate.so` (64-bit)
- `libs/linux/libTurboActivate.x86.so` (32-bit)

## Usage

```python
from src.licensing.turboactivate_integration import UsenetSyncLicense

# Initialize
license = UsenetSyncLicense()

# Check status
status = license.get_license_status()
print(f"Licensed: {status['licensed']}")

# Activate with key
success, msg = license.activate_with_key("YOUR-KEY-HERE")

# Start trial
success, msg = license.start_trial()

# Protect functions
@license.require_valid_license()
def protected_function():
    pass
```

## Important Files

- **TurboActivate.dat**: Contains your product configuration. This file is specific to UsenetSync and should not be modified or replaced.
- **Version GUID**: `lzyz4mi2lgoawqj5bkjjvjceygsqfdi` - This is embedded in the code and must match your LimeLM product configuration.

## Security Notes

1. The `TurboActivate.dat` file is safe to distribute with your application
2. Never share your Version GUID publicly (except in compiled code)
3. Always sign your binaries to prevent tampering
4. The libraries check for debuggers and virtual machines automatically

## Testing

Run the test script:
```bash
python src/licensing/turboactivate_integration.py
```

This will display the current license status and hardware ID.

## Support

- LimeLM Dashboard: https://wyday.com/limelm/
- Documentation: https://wyday.com/limelm/help/
- Support: support@wyday.com