# Mock Data Found and Fixes Required

## 1. StatusBar.tsx
**Status**: Partially fixed
- Mock server name changed to "Not configured" ✓
- Mock transfer stats generation needs to be removed

## 2. ConnectionPoolVisualization.tsx
**Status**: Fixed ✓
- Mock connections removed
- Shows empty state now

## 3. VersionHistory.tsx
**Status**: Needs fixing
- Contains mock version history data
- Should show empty array until backend provides real data

## 4. SearchBar.tsx
**Status**: Needs fixing
- Contains mock search results
- Should show empty results or real search results

## 5. main.rs - get_system_stats()
**Status**: Needs fixing
- Returns hardcoded values (CPU: 45.5%, Memory: 62.3%, etc.)
- Should use sysinfo crate to get real system stats

## 6. Dashboard.tsx
**Status**: Check needed
- Uses getSystemStats() which returns mock data
- Will be fixed once backend is fixed

## Manual Fixes Required:

### Fix 1: StatusBar.tsx
Remove lines 62-75 (the setInterval with Math.random)

### Fix 2: VersionHistory.tsx
Replace mock versions array (lines 65-105) with empty array

### Fix 3: SearchBar.tsx
Replace mock results (lines 96-132) with empty array

### Fix 4: main.rs
Replace get_system_stats implementation with real sysinfo calls