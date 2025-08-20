#!/bin/bash
# Rust Compilation Test Script
# Run this on a system with Rust installed

cd /workspace/usenet-sync-app/src-tauri

echo "🔨 Running cargo check..."
cargo check 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Compilation successful!"
    echo "🎉 The Rust code compiles without errors!"
else
    echo "❌ Compilation failed"
    echo "Please review the errors above"
fi
