#!/bin/bash

echo "Removing mock data from StatusBar..."
sed -i '60,78d' src/components/StatusBar.tsx
sed -i '60i\  // TODO: Replace with real transfer status from backend\n  useEffect(() => {\n    // Will be implemented when backend provides real transfer stats\n  }, []);' src/components/StatusBar.tsx

echo "Done!"
