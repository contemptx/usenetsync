// Test that our main.rs compiles by including it
// This will show any syntax errors in our code

#[path = "usenet-sync-app/src-tauri/src/main.rs"]
mod main_test;

fn main() {
    println!("If this compiles, the Rust code is valid!");
}