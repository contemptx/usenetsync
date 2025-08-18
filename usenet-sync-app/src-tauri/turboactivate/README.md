# TurboActivate Integration

For production builds, you need:

1. **TurboActivate Library Files**:
   - Windows: TurboActivate.dll (64-bit)
   - Linux: libTurboActivate.so
   - macOS: libTurboActivate.dylib

2. **TurboActivate.dat**: Your product-specific data file

3. **Header Files**: TurboActivate.h for C/C++ integration

## Download from:
- https://wyday.com/limelm/api/
- Select "TurboActivate SDK" for your platform

## Setup:
1. Download the SDK for your platform
2. Extract the library files to this directory
3. Place your TurboActivate.dat file here
4. Update build.rs to link the library

## Development Mode:
Currently using stubbed implementation for testing.
To enable real licensing, uncomment the linking in turboactivate.rs
