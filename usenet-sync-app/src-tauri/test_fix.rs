use sysinfo::System;

fn main() {
    let mut sys = System::new_all();
    sys.refresh_all();
    
    // Check correct API
    let disks = sys.disks();
    for disk in disks {
        println!("Disk: {:?}", disk.name());
    }
}
