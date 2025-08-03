"""
Settings and Configuration Dialog
Manages application settings and NNTP server configuration
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from pathlib import Path
from typing import Dict, Any, List

class SettingsDialog:
    """Dialog for application settings management"""
    
    def __init__(self, parent, backend):
        self.parent = parent
        self.backend = backend
        self.result = None
        self.config_data = {}
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("800x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self.load_configuration()
        self.create_widgets()
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
    
    def load_configuration(self):
        """Load current configuration"""
        try:
            config_file = Path("usenet_sync_config.json")
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.config_data = json.load(f)
            else:
                # Default configuration
                self.config_data = {
                    "servers": [],
                    "storage": {
                        "database_path": "data/usenetsync.db",
                        "temp_directory": "temp",
                        "log_directory": "logs"
                    },
                    "network": {
                        "max_connections": 4,
                        "timeout": 30,
                        "retry_attempts": 3
                    },
                    "processing": {
                        "segment_size": 768000,
                        "compression_enabled": True,
                        "parallel_uploads": 4
                    },
                    "gui": {
                        "theme": "default",
                        "auto_refresh": True,
                        "notifications": True,
                        "default_download_path": str(Path.home() / "Downloads")
                    }
                }
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {e}")
            self.config_data = {}
    
    def create_widgets(self):
        """Create settings dialog widgets"""
        # Settings notebook
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_servers_tab()
        self.create_network_tab()
        self.create_storage_tab()
        self.create_processing_tab()
        self.create_gui_tab()
        self.create_advanced_tab()
        
        # Buttons
        buttons_frame = ttk.Frame(self.dialog)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="Save Settings", 
                  command=self.save_settings, style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Test Connection", 
                  command=self.test_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Reset to Defaults", 
                  command=self.reset_defaults).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Cancel", 
                  command=self.on_cancel).pack(side=tk.RIGHT, padx=5)
    
    def create_servers_tab(self):
        """Create NNTP servers configuration tab"""
        servers_frame = ttk.Frame(self.notebook)
        self.notebook.add(servers_frame, text="NNTP Servers")
        
        # Header
        header_frame = ttk.Frame(servers_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text="NNTP Server Configuration", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W)
        ttk.Label(header_frame, text="Configure your Usenet server accounts for file uploading and downloading.",
                 wraplength=600).pack(anchor=tk.W, pady=5)
        
        # Servers list
        list_frame = ttk.LabelFrame(servers_frame, text="Configured Servers", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Servers tree
        self.servers_tree = ttk.Treeview(list_frame,
                                        columns=('hostname', 'port', 'ssl', 'enabled', 'priority'),
                                        show='headings')
        
        self.servers_tree.heading('hostname', text='Hostname')
        self.servers_tree.heading('port', text='Port')
        self.servers_tree.heading('ssl', text='SSL')
        self.servers_tree.heading('enabled', text='Enabled')
        self.servers_tree.heading('priority', text='Priority')
        
        self.servers_tree.column('hostname', width=200)
        self.servers_tree.column('port', width=60)
        self.servers_tree.column('ssl', width=50)
        self.servers_tree.column('enabled', width=70)
        self.servers_tree.column('priority', width=70)
        
        servers_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.servers_tree.yview)
        self.servers_tree.configure(yscrollcommand=servers_scroll.set)
        
        self.servers_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        servers_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate servers
        self.populate_servers_tree()
        
        # Server controls
        controls_frame = ttk.Frame(servers_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(controls_frame, text="Add Server", 
                  command=self.add_server).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="Edit Server", 
                  command=self.edit_server).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="Remove Server", 
                  command=self.remove_server).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="Test Selected", 
                  command=self.test_selected_server).pack(side=tk.LEFT, padx=10)
    
    def create_network_tab(self):
        """Create network settings tab"""
        network_frame = ttk.Frame(self.notebook)
        self.notebook.add(network_frame, text="Network")
        
        # Network settings
        settings_frame = ttk.LabelFrame(network_frame, text="Network Configuration", padding=15)
        settings_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Max connections
        ttk.Label(settings_frame, text="Max Connections per Server:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.max_connections_var = tk.StringVar(value=str(self.config_data.get('network', {}).get('max_connections', 4)))
        max_conn_spin = ttk.Spinbox(settings_frame, from_=1, to=20, textvariable=self.max_connections_var, width=10)
        max_conn_spin.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # Timeout
        ttk.Label(settings_frame, text="Connection Timeout (seconds):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.timeout_var = tk.StringVar(value=str(self.config_data.get('network', {}).get('timeout', 30)))
        timeout_spin = ttk.Spinbox(settings_frame, from_=5, to=120, textvariable=self.timeout_var, width=10)
        timeout_spin.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        # Retry attempts
        ttk.Label(settings_frame, text="Retry Attempts:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.retry_var = tk.StringVar(value=str(self.config_data.get('network', {}).get('retry_attempts', 3)))
        retry_spin = ttk.Spinbox(settings_frame, from_=0, to=10, textvariable=self.retry_var, width=10)
        retry_spin.grid(row=2, column=1, sticky=tk.W, padx=10)
        
        # SSL verification
        self.ssl_verify_var = tk.BooleanVar(value=self.config_data.get('network', {}).get('ssl_verify', True))
        ttk.Checkbutton(settings_frame, text="Verify SSL certificates", 
                       variable=self.ssl_verify_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # Proxy settings
        proxy_frame = ttk.LabelFrame(network_frame, text="Proxy Settings (Optional)", padding=15)
        proxy_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.use_proxy_var = tk.BooleanVar(value=self.config_data.get('network', {}).get('use_proxy', False))
        ttk.Checkbutton(proxy_frame, text="Use HTTP Proxy", 
                       variable=self.use_proxy_var, command=self.toggle_proxy).grid(row=0, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Label(proxy_frame, text="Proxy Host:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.proxy_host_var = tk.StringVar(value=self.config_data.get('network', {}).get('proxy_host', ''))
        proxy_host_entry = ttk.Entry(proxy_frame, textvariable=self.proxy_host_var, width=30)
        proxy_host_entry.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(proxy_frame, text="Proxy Port:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.proxy_port_var = tk.StringVar(value=str(self.config_data.get('network', {}).get('proxy_port', 8080)))
        proxy_port_entry = ttk.Entry(proxy_frame, textvariable=self.proxy_port_var, width=10)
        proxy_port_entry.grid(row=2, column=1, sticky=tk.W, padx=10)
        
        self.proxy_widgets = [proxy_host_entry, proxy_port_entry]
        self.toggle_proxy()
    
    def create_storage_tab(self):
        """Create storage settings tab"""
        storage_frame = ttk.Frame(self.notebook)
        self.notebook.add(storage_frame, text="Storage")
        
        # Storage paths
        paths_frame = ttk.LabelFrame(storage_frame, text="Storage Locations", padding=15)
        paths_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Database path
        ttk.Label(paths_frame, text="Database File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.db_path_var = tk.StringVar(value=self.config_data.get('storage', {}).get('database_path', ''))
        db_path_entry = ttk.Entry(paths_frame, textvariable=self.db_path_var, width=50)
        db_path_entry.grid(row=0, column=1, sticky=tk.W, padx=10)
        ttk.Button(paths_frame, text="Browse", 
                  command=lambda: self.browse_file(self.db_path_var, "Database Files", "*.db")).grid(row=0, column=2)
        
        # Temp directory
        ttk.Label(paths_frame, text="Temp Directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.temp_dir_var = tk.StringVar(value=self.config_data.get('storage', {}).get('temp_directory', ''))
        temp_dir_entry = ttk.Entry(paths_frame, textvariable=self.temp_dir_var, width=50)
        temp_dir_entry.grid(row=1, column=1, sticky=tk.W, padx=10)
        ttk.Button(paths_frame, text="Browse", 
                  command=lambda: self.browse_directory(self.temp_dir_var, "Select Temp Directory")).grid(row=1, column=2)
        
        # Log directory
        ttk.Label(paths_frame, text="Log Directory:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.log_dir_var = tk.StringVar(value=self.config_data.get('storage', {}).get('log_directory', ''))
        log_dir_entry = ttk.Entry(paths_frame, textvariable=self.log_dir_var, width=50)
        log_dir_entry.grid(row=2, column=1, sticky=tk.W, padx=10)
        ttk.Button(paths_frame, text="Browse", 
                  command=lambda: self.browse_directory(self.log_dir_var, "Select Log Directory")).grid(row=2, column=2)
        
        # Storage options
        options_frame = ttk.LabelFrame(storage_frame, text="Storage Options", padding=15)
        options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Auto cleanup
        self.auto_cleanup_var = tk.BooleanVar(value=self.config_data.get('storage', {}).get('auto_cleanup', True))
        ttk.Checkbutton(options_frame, text="Auto-cleanup temporary files", 
                       variable=self.auto_cleanup_var).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Cleanup interval
        ttk.Label(options_frame, text="Cleanup Interval (hours):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.cleanup_interval_var = tk.StringVar(value=str(self.config_data.get('storage', {}).get('cleanup_interval', 24)))
        cleanup_spin = ttk.Spinbox(options_frame, from_=1, to=168, textvariable=self.cleanup_interval_var, width=10)
        cleanup_spin.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        # Max cache size
        ttk.Label(options_frame, text="Max Cache Size (MB):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.cache_size_var = tk.StringVar(value=str(self.config_data.get('storage', {}).get('max_cache_size', 1000)))
        cache_spin = ttk.Spinbox(options_frame, from_=100, to=10000, textvariable=self.cache_size_var, width=10)
        cache_spin.grid(row=2, column=1, sticky=tk.W, padx=10)
    
    def create_processing_tab(self):
        """Create processing settings tab"""
        processing_frame = ttk.Frame(self.notebook)
        self.notebook.add(processing_frame, text="Processing")
        
        # Segmentation settings
        segment_frame = ttk.LabelFrame(processing_frame, text="File Segmentation", padding=15)
        segment_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Segment size
        ttk.Label(segment_frame, text="Segment Size (KB):").grid(row=0, column=0, sticky=tk.W, pady=5)
        segment_size_kb = self.config_data.get('processing', {}).get('segment_size', 768000) // 1024
        self.segment_size_var = tk.StringVar(value=str(segment_size_kb))
        segment_size_combo = ttk.Combobox(segment_frame, textvariable=self.segment_size_var,
                                         values=["256", "512", "750", "1024", "1536"], width=10)
        segment_size_combo.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # Compression
        self.compression_var = tk.BooleanVar(value=self.config_data.get('processing', {}).get('compression_enabled', True))
        ttk.Checkbutton(segment_frame, text="Enable compression", 
                       variable=self.compression_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Redundancy
        ttk.Label(segment_frame, text="Redundancy Level:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.redundancy_var = tk.StringVar(value=str(self.config_data.get('processing', {}).get('redundancy_level', 0)))
        redundancy_combo = ttk.Combobox(segment_frame, textvariable=self.redundancy_var,
                                       values=["0", "1", "2", "3"], width=10, state="readonly")
        redundancy_combo.grid(row=2, column=1, sticky=tk.W, padx=10)
        
        # Performance settings
        perf_frame = ttk.LabelFrame(processing_frame, text="Performance", padding=15)
        perf_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Parallel uploads
        ttk.Label(perf_frame, text="Parallel Upload Threads:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.parallel_uploads_var = tk.StringVar(value=str(self.config_data.get('processing', {}).get('parallel_uploads', 4)))
        parallel_spin = ttk.Spinbox(perf_frame, from_=1, to=10, textvariable=self.parallel_uploads_var, width=10)
        parallel_spin.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # Max memory usage
        ttk.Label(perf_frame, text="Max Memory Usage (MB):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.max_memory_var = tk.StringVar(value=str(self.config_data.get('processing', {}).get('max_memory_mb', 2048)))
        memory_spin = ttk.Spinbox(perf_frame, from_=512, to=8192, textvariable=self.max_memory_var, width=10)
        memory_spin.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        # Queue management
        queue_frame = ttk.LabelFrame(processing_frame, text="Queue Management", padding=15)
        queue_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Max queue size
        ttk.Label(queue_frame, text="Max Queue Size:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.max_queue_var = tk.StringVar(value=str(self.config_data.get('processing', {}).get('max_queue_size', 1000)))
        queue_spin = ttk.Spinbox(queue_frame, from_=100, to=10000, textvariable=self.max_queue_var, width=10)
        queue_spin.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # Auto retry
        self.auto_retry_var = tk.BooleanVar(value=self.config_data.get('processing', {}).get('auto_retry_failed', True))
        ttk.Checkbutton(queue_frame, text="Auto-retry failed uploads", 
                       variable=self.auto_retry_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
    
    def create_gui_tab(self):
        """Create GUI settings tab"""
        gui_frame = ttk.Frame(self.notebook)
        self.notebook.add(gui_frame, text="Interface")
        
        # Appearance settings
        appearance_frame = ttk.LabelFrame(gui_frame, text="Appearance", padding=15)
        appearance_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Theme
        ttk.Label(appearance_frame, text="Theme:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.theme_var = tk.StringVar(value=self.config_data.get('gui', {}).get('theme', 'default'))
        theme_combo = ttk.Combobox(appearance_frame, textvariable=self.theme_var,
                                  values=["default", "dark", "light"], width=15, state="readonly")
        theme_combo.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # Font size
        ttk.Label(appearance_frame, text="Font Size:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.font_size_var = tk.StringVar(value=str(self.config_data.get('gui', {}).get('font_size', 9)))
        font_size_combo = ttk.Combobox(appearance_frame, textvariable=self.font_size_var,
                                      values=["8", "9", "10", "11", "12"], width=10, state="readonly")
        font_size_combo.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        # Default download path
        ttk.Label(appearance_frame, text="Default Download Path:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.download_path_var = tk.StringVar(value=self.config_data.get('gui', {}).get('default_download_path', ''))
        download_path_entry = ttk.Entry(appearance_frame, textvariable=self.download_path_var, width=40)
        download_path_entry.grid(row=2, column=1, sticky=tk.W, padx=10)
        ttk.Button(appearance_frame, text="Browse", 
                  command=lambda: self.browse_directory(self.download_path_var, "Select Download Directory")).grid(row=2, column=2)
        
        # Behavior settings
        behavior_frame = ttk.LabelFrame(gui_frame, text="Behavior", padding=15)
        behavior_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Auto refresh
        self.auto_refresh_var = tk.BooleanVar(value=self.config_data.get('gui', {}).get('auto_refresh', True))
        ttk.Checkbutton(behavior_frame, text="Auto-refresh folder contents", 
                       variable=self.auto_refresh_var).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Notifications
        self.notifications_var = tk.BooleanVar(value=self.config_data.get('gui', {}).get('notifications', True))
        ttk.Checkbutton(behavior_frame, text="Show desktop notifications", 
                       variable=self.notifications_var).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # Confirm deletions
        self.confirm_delete_var = tk.BooleanVar(value=self.config_data.get('gui', {}).get('confirm_deletions', True))
        ttk.Checkbutton(behavior_frame, text="Confirm before deleting items", 
                       variable=self.confirm_delete_var).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # Auto-save settings
        self.auto_save_var = tk.BooleanVar(value=self.config_data.get('gui', {}).get('auto_save_settings', True))
        ttk.Checkbutton(behavior_frame, text="Auto-save settings on changes", 
                       variable=self.auto_save_var).grid(row=3, column=0, sticky=tk.W, pady=5)
        
        # Performance settings
        perf_frame = ttk.LabelFrame(gui_frame, text="Performance", padding=15)
        perf_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # File browser page size
        ttk.Label(perf_frame, text="File Browser Page Size:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.page_size_var = tk.StringVar(value=str(self.config_data.get('gui', {}).get('file_browser_page_size', 1000)))
        page_size_combo = ttk.Combobox(perf_frame, textvariable=self.page_size_var,
                                      values=["100", "500", "1000", "2000", "5000"], width=10)
        page_size_combo.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # Refresh interval
        ttk.Label(perf_frame, text="Auto-refresh Interval (seconds):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.refresh_interval_var = tk.StringVar(value=str(self.config_data.get('gui', {}).get('refresh_interval', 30)))
        refresh_spin = ttk.Spinbox(perf_frame, from_=5, to=300, textvariable=self.refresh_interval_var, width=10)
        refresh_spin.grid(row=1, column=1, sticky=tk.W, padx=10)
    
    def create_advanced_tab(self):
        """Create advanced settings tab"""
        advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(advanced_frame, text="Advanced")
        
        # Logging settings
        logging_frame = ttk.LabelFrame(advanced_frame, text="Logging", padding=15)
        logging_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Log level
        ttk.Label(logging_frame, text="Log Level:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.log_level_var = tk.StringVar(value=self.config_data.get('logging', {}).get('level', 'INFO'))
        log_level_combo = ttk.Combobox(logging_frame, textvariable=self.log_level_var,
                                      values=["DEBUG", "INFO", "WARNING", "ERROR"], width=10, state="readonly")
        log_level_combo.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # Max log size
        ttk.Label(logging_frame, text="Max Log File Size (MB):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.max_log_size_var = tk.StringVar(value=str(self.config_data.get('logging', {}).get('max_size_mb', 10)))
        log_size_spin = ttk.Spinbox(logging_frame, from_=1, to=100, textvariable=self.max_log_size_var, width=10)
        log_size_spin.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        # Keep log files
        ttk.Label(logging_frame, text="Keep Log Files (count):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.keep_logs_var = tk.StringVar(value=str(self.config_data.get('logging', {}).get('backup_count', 5)))
        keep_logs_spin = ttk.Spinbox(logging_frame, from_=1, to=20, textvariable=self.keep_logs_var, width=10)
        keep_logs_spin.grid(row=2, column=1, sticky=tk.W, padx=10)
        
        # Security settings
        security_frame = ttk.LabelFrame(advanced_frame, text="Security", padding=15)
        security_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Key size
        ttk.Label(security_frame, text="RSA Key Size:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.key_size_var = tk.StringVar(value=str(self.config_data.get('security', {}).get('key_size', 4096)))
        key_size_combo = ttk.Combobox(security_frame, textvariable=self.key_size_var,
                                     values=["2048", "3072", "4096"], width=10, state="readonly")
        key_size_combo.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # Encryption algorithm
        ttk.Label(security_frame, text="Encryption Algorithm:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.encryption_var = tk.StringVar(value=self.config_data.get('security', {}).get('encryption_algorithm', 'AES-256'))
        encryption_combo = ttk.Combobox(security_frame, textvariable=self.encryption_var,
                                       values=["AES-128", "AES-192", "AES-256"], width=15, state="readonly")
        encryption_combo.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        # Database settings
        database_frame = ttk.LabelFrame(advanced_frame, text="Database", padding=15)
        database_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Connection pool size
        ttk.Label(database_frame, text="Connection Pool Size:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.pool_size_var = tk.StringVar(value=str(self.config_data.get('database', {}).get('pool_size', 10)))
        pool_size_spin = ttk.Spinbox(database_frame, from_=1, to=50, textvariable=self.pool_size_var, width=10)
        pool_size_spin.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # Auto vacuum
        self.auto_vacuum_var = tk.BooleanVar(value=self.config_data.get('database', {}).get('auto_vacuum', True))
        ttk.Checkbutton(database_frame, text="Auto-vacuum database", 
                       variable=self.auto_vacuum_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Backup settings
        backup_frame = ttk.LabelFrame(advanced_frame, text="Backup", padding=15)
        backup_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Auto backup
        self.auto_backup_var = tk.BooleanVar(value=self.config_data.get('backup', {}).get('auto_backup', False))
        ttk.Checkbutton(backup_frame, text="Enable automatic backups", 
                       variable=self.auto_backup_var, command=self.toggle_backup).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Backup interval
        ttk.Label(backup_frame, text="Backup Interval (hours):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.backup_interval_var = tk.StringVar(value=str(self.config_data.get('backup', {}).get('interval_hours', 24)))
        backup_interval_spin = ttk.Spinbox(backup_frame, from_=1, to=168, textvariable=self.backup_interval_var, width=10)
        backup_interval_spin.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        # Backup location
        ttk.Label(backup_frame, text="Backup Location:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.backup_location_var = tk.StringVar(value=self.config_data.get('backup', {}).get('location', ''))
        backup_location_entry = ttk.Entry(backup_frame, textvariable=self.backup_location_var, width=40)
        backup_location_entry.grid(row=2, column=1, sticky=tk.W, padx=10)
        ttk.Button(backup_frame, text="Browse", 
                  command=lambda: self.browse_directory(self.backup_location_var, "Select Backup Directory")).grid(row=2, column=2)
        
        self.backup_widgets = [backup_interval_spin, backup_location_entry]
        self.toggle_backup()
    
    def populate_servers_tree(self):
        """Populate servers tree with current servers"""
        # Clear existing items
        for item in self.servers_tree.get_children():
            self.servers_tree.delete(item)
        
        # Add servers
        servers = self.config_data.get('servers', [])
        for server in servers:
            ssl_status = "✓" if server.get('use_ssl', False) else "✗"
            enabled_status = "✓" if server.get('enabled', True) else "✗"
            
            self.servers_tree.insert('', 'end', values=(
                server.get('hostname', ''),
                server.get('port', ''),
                ssl_status,
                enabled_status,
                server.get('priority', 1)
            ), tags=(str(len(self.servers_tree.get_children())),))
    
    def add_server(self):
        """Add new server"""
        server_dialog = ServerConfigDialog(self.dialog, {})
        if server_dialog.result:
            servers = self.config_data.setdefault('servers', [])
            servers.append(server_dialog.result)
            self.populate_servers_tree()
    
    def edit_server(self):
        """Edit selected server"""
        selection = self.servers_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a server to edit")
            return
        
        item = self.servers_tree.item(selection[0])
        server_index = int(item['tags'][0])
        
        servers = self.config_data.get('servers', [])
        if server_index < len(servers):
            server_dialog = ServerConfigDialog(self.dialog, servers[server_index])
            if server_dialog.result:
                servers[server_index] = server_dialog.result
                self.populate_servers_tree()
    
    def remove_server(self):
        """Remove selected server"""
        selection = self.servers_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a server to remove")
            return
        
        result = messagebox.askyesno("Confirm", "Remove selected server?")
        if result:
            item = self.servers_tree.item(selection[0])
            server_index = int(item['tags'][0])
            
            servers = self.config_data.get('servers', [])
            if server_index < len(servers):
                del servers[server_index]
                self.populate_servers_tree()
    
    def test_selected_server(self):
        """Test selected server connection"""
        selection = self.servers_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a server to test")
            return
        
        item = self.servers_tree.item(selection[0])
        server_index = int(item['tags'][0])
        
        servers = self.config_data.get('servers', [])
        if server_index < len(servers):
            server = servers[server_index]
            
            # TODO: Implement server testing
            messagebox.showinfo("Test Result", f"Testing connection to {server.get('hostname', 'Unknown')}...")
    
    def toggle_proxy(self):
        """Toggle proxy settings widgets"""
        state = tk.NORMAL if self.use_proxy_var.get() else tk.DISABLED
        for widget in self.proxy_widgets:
            widget.config(state=state)
    
    def toggle_backup(self):
        """Toggle backup settings widgets"""
        state = tk.NORMAL if self.auto_backup_var.get() else tk.DISABLED
        for widget in self.backup_widgets:
            widget.config(state=state)
    
    def browse_file(self, var, title, filetypes):
        """Browse for file"""
        filename = filedialog.asksaveasfilename(title=title, filetypes=[(title, filetypes)])
        if filename:
            var.set(filename)
    
    def browse_directory(self, var, title):
        """Browse for directory"""
        directory = filedialog.askdirectory(title=title, initialdir=var.get())
        if directory:
            var.set(directory)
    
    def save_settings(self):
        """Save all settings"""
        try:
            # Update config data with current values
            self.update_config_from_widgets()
            
            # Save to file
            config_file = Path("usenet_sync_config.json")
            with open(config_file, 'w') as f:
                json.dump(self.config_data, f, indent=2)
            
            self.result = True
            messagebox.showinfo("Settings Saved", "Settings have been saved successfully.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def update_config_from_widgets(self):
        """Update config data from widget values"""
        # Network settings
        network = self.config_data.setdefault('network', {})
        network['max_connections'] = int(self.max_connections_var.get())
        network['timeout'] = int(self.timeout_var.get())
        network['retry_attempts'] = int(self.retry_var.get())
        network['ssl_verify'] = self.ssl_verify_var.get()
        network['use_proxy'] = self.use_proxy_var.get()
        network['proxy_host'] = self.proxy_host_var.get()
        network['proxy_port'] = int(self.proxy_port_var.get()) if self.proxy_port_var.get() else 8080
        
        # Storage settings
        storage = self.config_data.setdefault('storage', {})
        storage['database_path'] = self.db_path_var.get()
        storage['temp_directory'] = self.temp_dir_var.get()
        storage['log_directory'] = self.log_dir_var.get()
        storage['auto_cleanup'] = self.auto_cleanup_var.get()
        storage['cleanup_interval'] = int(self.cleanup_interval_var.get())
        storage['max_cache_size'] = int(self.cache_size_var.get())
        
        # Processing settings
        processing = self.config_data.setdefault('processing', {})
        processing['segment_size'] = int(self.segment_size_var.get()) * 1024  # Convert KB to bytes
        processing['compression_enabled'] = self.compression_var.get()
        processing['redundancy_level'] = int(self.redundancy_var.get())
        processing['parallel_uploads'] = int(self.parallel_uploads_var.get())
        processing['max_memory_mb'] = int(self.max_memory_var.get())
        processing['max_queue_size'] = int(self.max_queue_var.get())
        processing['auto_retry_failed'] = self.auto_retry_var.get()
        
        # GUI settings
        gui = self.config_data.setdefault('gui', {})
        gui['theme'] = self.theme_var.get()
        gui['font_size'] = int(self.font_size_var.get())
        gui['default_download_path'] = self.download_path_var.get()
        gui['auto_refresh'] = self.auto_refresh_var.get()
        gui['notifications'] = self.notifications_var.get()
        gui['confirm_deletions'] = self.confirm_delete_var.get()
        gui['auto_save_settings'] = self.auto_save_var.get()
        gui['file_browser_page_size'] = int(self.page_size_var.get())
        gui['refresh_interval'] = int(self.refresh_interval_var.get())
        
        # Advanced settings
        logging_config = self.config_data.setdefault('logging', {})
        logging_config['level'] = self.log_level_var.get()
        logging_config['max_size_mb'] = int(self.max_log_size_var.get())
        logging_config['backup_count'] = int(self.keep_logs_var.get())
        
        security = self.config_data.setdefault('security', {})
        security['key_size'] = int(self.key_size_var.get())
        security['encryption_algorithm'] = self.encryption_var.get()
        
        database = self.config_data.setdefault('database', {})
        database['pool_size'] = int(self.pool_size_var.get())
        database['auto_vacuum'] = self.auto_vacuum_var.get()
        
        backup = self.config_data.setdefault('backup', {})
        backup['auto_backup'] = self.auto_backup_var.get()
        backup['interval_hours'] = int(self.backup_interval_var.get())
        backup['location'] = self.backup_location_var.get()
    
    def test_connection(self):
        """Test NNTP connection with current settings"""
        if not self.backend:
            messagebox.showerror("Error", "Backend not available")
            return
        
        messagebox.showinfo("Test Connection", "Testing connection with current settings...")
        # TODO: Implement connection test
    
    def reset_defaults(self):
        """Reset settings to defaults"""
        result = messagebox.askyesno("Reset Settings", 
                                    "Reset all settings to default values? This cannot be undone.")
        if result:
            # Reset config data
            self.config_data = {}
            self.load_configuration()  # This will load defaults
            
            # Refresh all widgets
            # TODO: Implement widget refresh
            messagebox.showinfo("Reset Complete", "Settings have been reset to defaults.")
    
    def on_cancel(self):
        """Handle dialog cancellation"""
        self.dialog.destroy()

class ServerConfigDialog:
    """Dialog for configuring individual NNTP server"""
    
    def __init__(self, parent, server_data):
        self.parent = parent
        self.server_data = server_data.copy()
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Server Configuration")
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 100,
            parent.winfo_rooty() + 100
        ))
        
        self.create_widgets()
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
    
    def create_widgets(self):
        """Create server configuration widgets"""
        # Header
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(header_frame, text="NNTP Server Configuration", 
                 font=('Arial', 12, 'bold')).pack()
        
        # Server settings
        settings_frame = ttk.LabelFrame(self.dialog, text="Server Settings", padding=15)
        settings_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Server name
        ttk.Label(settings_frame, text="Server Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=self.server_data.get('name', ''))
        name_entry = ttk.Entry(settings_frame, textvariable=self.name_var, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.W, padx=10)
        name_entry.focus()
        
        # Hostname
        ttk.Label(settings_frame, text="Hostname:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.hostname_var = tk.StringVar(value=self.server_data.get('hostname', ''))
        hostname_entry = ttk.Entry(settings_frame, textvariable=self.hostname_var, width=30)
        hostname_entry.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        # Port
        ttk.Label(settings_frame, text="Port:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.port_var = tk.StringVar(value=str(self.server_data.get('port', 563)))
        port_entry = ttk.Entry(settings_frame, textvariable=self.port_var, width=10)
        port_entry.grid(row=2, column=1, sticky=tk.W, padx=10)
        
        # SSL
        self.ssl_var = tk.BooleanVar(value=self.server_data.get('use_ssl', True))
        ttk.Checkbutton(settings_frame, text="Use SSL/TLS", 
                       variable=self.ssl_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Authentication
        auth_frame = ttk.LabelFrame(self.dialog, text="Authentication", padding=15)
        auth_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Username
        ttk.Label(auth_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar(value=self.server_data.get('username', ''))
        username_entry = ttk.Entry(auth_frame, textvariable=self.username_var, width=30)
        username_entry.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # Password
        ttk.Label(auth_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar(value=self.server_data.get('password', ''))
        password_entry = ttk.Entry(auth_frame, textvariable=self.password_var, show="*", width=30)
        password_entry.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        # Advanced settings
        advanced_frame = ttk.LabelFrame(self.dialog, text="Advanced Settings", padding=15)
        advanced_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Max connections
        ttk.Label(advanced_frame, text="Max Connections:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.max_conn_var = tk.StringVar(value=str(self.server_data.get('max_connections', 4)))
        max_conn_spin = ttk.Spinbox(advanced_frame, from_=1, to=20, textvariable=self.max_conn_var, width=10)
        max_conn_spin.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # Priority
        ttk.Label(advanced_frame, text="Priority:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.priority_var = tk.StringVar(value=str(self.server_data.get('priority', 1)))
        priority_spin = ttk.Spinbox(advanced_frame, from_=1, to=10, textvariable=self.priority_var, width=10)
        priority_spin.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        # Posting group
        ttk.Label(advanced_frame, text="Posting Group:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.posting_group_var = tk.StringVar(value=self.server_data.get('posting_group', 'alt.binaries.test'))
        posting_group_entry = ttk.Entry(advanced_frame, textvariable=self.posting_group_var, width=30)
        posting_group_entry.grid(row=2, column=1, sticky=tk.W, padx=10)
        
        # Enabled
        self.enabled_var = tk.BooleanVar(value=self.server_data.get('enabled', True))
        ttk.Checkbutton(advanced_frame, text="Server enabled", 
                       variable=self.enabled_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # Buttons
        buttons_frame = ttk.Frame(self.dialog)
        buttons_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Button(buttons_frame, text="Test Connection", 
                  command=self.test_connection).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Save", 
                  command=self.save_server, style='Primary.TButton').pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", 
                  command=self.on_cancel).pack(side=tk.RIGHT, padx=5)
    
    def test_connection(self):
        """Test server connection"""
        # Validate inputs
        if not self.hostname_var.get().strip():
            messagebox.showerror("Error", "Hostname is required")
            return
        
        if not self.port_var.get().strip():
            messagebox.showerror("Error", "Port is required")
            return
        
        try:
            port = int(self.port_var.get())
            if port < 1 or port > 65535:
                raise ValueError("Invalid port range")
        except ValueError:
            messagebox.showerror("Error", "Port must be a number between 1 and 65535")
            return
        
        # TODO: Implement actual connection test
        messagebox.showinfo("Test Result", "Connection test not yet implemented")
    
    def save_server(self):
        """Save server configuration"""
        # Validate inputs
        if not self.name_var.get().strip():
            messagebox.showerror("Error", "Server name is required")
            return
        
        if not self.hostname_var.get().strip():
            messagebox.showerror("Error", "Hostname is required")
            return
        
        try:
            port = int(self.port_var.get())
            if port < 1 or port > 65535:
                raise ValueError("Invalid port range")
        except ValueError:
            messagebox.showerror("Error", "Port must be a number between 1 and 65535")
            return
        
        # Create server config
        self.result = {
            'name': self.name_var.get().strip(),
            'hostname': self.hostname_var.get().strip(),
            'port': port,
            'username': self.username_var.get().strip(),
            'password': self.password_var.get(),
            'use_ssl': self.ssl_var.get(),
            'max_connections': int(self.max_conn_var.get()),
            'priority': int(self.priority_var.get()),
            'posting_group': self.posting_group_var.get().strip(),
            'enabled': self.enabled_var.get()
        }
        
        self.dialog.destroy()
    
    def on_cancel(self):
        """Handle dialog cancellation"""
        self.dialog.destroy()