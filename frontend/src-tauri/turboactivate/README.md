# TurboActivate Integration

## Current Status: Development Mode

The application is currently configured to run without TurboActivate licensing for development and testing purposes.

## For Production Deployment

To enable real licensing in production, you need:

### 1. Required Files from wyDay

You need to obtain these files from your LimeLM account at https://wyday.com/limelm/:

- **TurboActivate.dll** (Windows 64-bit)
- **libTurboActivate.so** (Linux)  
- **libTurboActivate.dylib** (macOS)
- **TurboActivate.dat** (Your product-specific data file)
- **TurboActivate.h** (C header file for reference)

### 2. File Placement

Place the files in this directory structure:
```
turboactivate/
├── windows/
│   └── TurboActivate.dll
├── linux/
│   └── libTurboActivate.so
├── macos/
│   └── libTurboActivate.dylib
└── TurboActivate.dat
```

### 3. Enable TurboActivate in Code

1. In `Cargo.toml`, add the feature flag:
   ```toml
   [features]
   turboactivate = []
   ```

2. In `src/turboactivate.rs`, uncomment the `#[link]` directive:
   ```rust
   #[link(name = "TurboActivate")]
   extern "C" {
       // ... function declarations
   }
   ```

3. Build with the feature enabled:
   ```bash
   cargo build --release --features turboactivate
   ```

### 4. Build Script Configuration

The `build.rs` is already configured to link TurboActivate when the feature is enabled.

## Development Mode

Currently using a stubbed implementation that:
- Allows the application to run without licensing
- Provides mock license validation
- Generates hardware IDs based on system info
- Returns default feature values

## Testing License Features

Even in development mode, you can test:
- License activation flow
- Trial period management
- Hardware ID generation
- Feature flag checks

The mock implementation accepts any license key in format: `XXXX-XXXX-XXXX-XXXX`

## Support

For TurboActivate SDK and licensing questions:
- Documentation: https://wyday.com/limelm/help/
- API Reference: https://wyday.com/limelm/api/
- Support: https://wyday.com/forum/