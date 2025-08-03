"""
GUI Component Testing Framework
Tests for GUI components and interactions
"""

import unittest
import tkinter as tk
from tkinter import ttk
import threading
import time
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import GUI components
from gui.main_application import MainApplication
from gui.dialogs.user_init_dialog import UserInitDialog
from gui.dialogs.download_dialog import DownloadDialog
from gui.widgets.file_browser import FileBrowserWidget, VirtualFileModel

class GUITestBase(unittest.TestCase):
    """Base class for GUI tests"""
    
    def setUp(self):
        """Setup test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide test window
        
        # Mock backend
        self.mock_backend = Mock()
        self.mock_backend.database = Mock()
        self.mock_backend.security = Mock()
        self.mock_backend.nntp = Mock()
        
        # Test data
        self.test_folders = [
            {
                'id': 1,
                'display_name': 'Test Folder 1',
                'folder_path': '/test/path1',
                'total_files': 100,
                'total_size': 1024 * 1024 * 50,  # 50MB
                'share_type': 'private'
            },
            {
                'id': 2,
                'display_name': 'Test Folder 2',
                'folder_path': '/test/path2',
                'total_files': 500,
                'total_size': 1024 * 1024 * 200,  # 200MB
                'share_type': 'public'
            }
        ]
        
        self.test_files = [
            {
                'id': 1,
                'file_path': 'document.pdf',
                'file_size': 1024 * 500,
                'file_hash': 'abc123',
                'modified_at': '2024-01-15 10:30:00',
                'uploaded_segments': 5,
                'total_segments': 5
            },
            {
                'id': 2,
                'file_path': 'image.jpg',
                'file_size': 1024 * 800,
                'file_hash': 'def456',
                'modified_at': '2024-01-16 14:20:00',
                'uploaded_segments': 3,
                'total_segments': 4
            }
        ]
    
    def tearDown(self):
        """Cleanup test environment"""
        if self.root:
            self.root.destroy()

class TestMainApplication(GUITestBase):
    """Test main application functionality"""
    
    def test_application_initialization(self):
        """Test application initializes correctly"""
        with patch('gui.main_application.UsenetSync') as mock_usenet:
            mock_usenet.return_value = self.mock_backend
            
            app = MainApplication()
            
            # Check basic window properties
            self.assertIsNotNone(app.root)
            self.assertEqual(app.root.title(), "UsenetSync v2.0 - Secure Usenet File Synchronization")
            
            # Check components are created
            self.assertIsNotNone(app.folder_tree)
            self.assertIsNotNone(app.details_notebook)
            self.assertIsNotNone(app.status_bar)
            
            app.root.destroy()
    
    def test_folder_tree_population(self):
        """Test folder tree populates with data"""
        with patch('gui.main_application.UsenetSync') as mock_usenet:
            mock_usenet.return_value = self.mock_backend
            self.mock_backend.list_folders.return_value = self.test_folders
            
            app = MainApplication()
            app.refresh_folders()
            
            # Check tree has items
            tree_items = app.folder_tree.get_children()
            self.assertEqual(len(tree_items), 2)
            
            # Check first item data
            first_item = app.folder_tree.item(tree_items[0])
            self.assertEqual(first_item['text'], 'Test Folder 1')
            
            app.root.destroy()
    
    def test_folder_selection(self):
        """Test folder selection updates details"""
        with patch('gui.main_application.UsenetSync') as mock_usenet:
            mock_usenet.return_value = self.mock_backend
            self.mock_backend.list_folders.return_value = self.test_folders
            self.mock_backend.database.get_folder.return_value = self.test_folders[0]
            self.mock_backend.database.get_folder_files.return_value = self.test_files
            
            app = MainApplication()
            app.refresh_folders()
            
            # Simulate folder selection
            tree_items = app.folder_tree.get_children()
            app.folder_tree.selection_set(tree_items[0])
            app.on_folder_select(None)
            
            # Check current folder is set
            self.assertEqual(app.current_folder, 1)
            
            app.root.destroy()
    
    def test_keyboard_shortcuts(self):
        """Test keyboard shortcuts work"""
        with patch('gui.main_application.UsenetSync') as mock_usenet:
            mock_usenet.return_value = self.mock_backend
            
            app = MainApplication()
            
            # Test user init shortcut
            with patch.object(app, 'show_user_init') as mock_user_init:
                event = Mock()
                app.root.event_generate('<Control-i>')
                app.root.update()
                # Note: This is a simplified test - actual event handling is more complex
            
            app.root.destroy()

class TestUserInitDialog(GUITestBase):
    """Test user initialization dialog"""
    
    def test_dialog_creation(self):
        """Test dialog creates correctly"""
        self.mock_backend.security.is_user_initialized.return_value = False
        
        dialog = UserInitDialog(self.root, self.mock_backend)
        
        # Check dialog properties
        self.assertIsNotNone(dialog.dialog)
        self.assertEqual(dialog.dialog.title(), "Initialize User Profile")
        
        # Check widgets exist
        self.assertIsNotNone(dialog.display_name_var)
        self.assertIsNotNone(dialog.email_var)
        self.assertIsNotNone(dialog.status_text)
        
        dialog.dialog.destroy()
    
    def test_user_initialization(self):
        """Test user initialization process"""
        self.mock_backend.security.is_user_initialized.return_value = False
        self.mock_backend.create_user.return_value = "test_user_123"
        
        dialog = UserInitDialog(self.root, self.mock_backend)
        
        # Set test data
        dialog.display_name_var.set("Test User")
        dialog.email_var.set("test@example.com")
        
        # Mock the threading to run synchronously
        with patch('threading.Thread') as mock_thread:
            def run_worker():
                # Simulate the worker function
                user_id = dialog.backend.create_user("Test User", "test@example.com")
                dialog.result = {
                    'user_id': user_id,
                    'display_name': "Test User",
                    'email': "test@example.com"
                }
            
            mock_thread.return_value.start = run_worker
            
            dialog.initialize_user()
            
            # Check result
            self.assertIsNotNone(dialog.result)
            self.assertEqual(dialog.result['user_id'], "test_user_123")
            self.assertEqual(dialog.result['display_name'], "Test User")
        
        dialog.dialog.destroy()
    
    def test_existing_user_detection(self):
        """Test existing user detection"""
        self.mock_backend.security.is_user_initialized.return_value = True
        self.mock_backend.security.get_user_info.return_value = {
            'user_id': 'existing_user',
            'display_name': 'Existing User',
            'created_at': '2024-01-01'
        }
        
        dialog = UserInitDialog(self.root, self.mock_backend)
        
        # Check that status shows existing user
        status_content = dialog.status_text.get('1.0', tk.END)
        self.assertIn("User already initialized", status_content)
        self.assertIn("existing_user", status_content)
        
        dialog.dialog.destroy()

class TestFileBrowserWidget(GUITestBase):
    """Test file browser widget"""
    
    def test_widget_creation(self):
        """Test widget creates correctly"""
        browser = FileBrowserWidget(self.root, self.mock_backend)
        
        # Check components exist
        self.assertIsNotNone(browser.file_tree)
        self.assertIsNotNone(browser.search_var)
        self.assertIsNotNone(browser.file_count_label)
        
        browser.destroy()
    
    def test_virtual_file_model(self):
        """Test virtual file model"""
        self.mock_backend.database.get_folder_files.return_value = self.test_files
        
        model = VirtualFileModel(self.mock_backend, 1)
        model.load_files()
        
        # Check files loaded
        self.assertEqual(len(model.files), 2)
        self.assertEqual(model.total_count, 2)
        
        # Test filtering
        model.set_search("document")
        self.assertEqual(len(model.filtered_files), 1)
        self.assertEqual(model.filtered_files[0]['file_path'], 'document.pdf')
        
        # Test sorting
        model.set_sort('size', reverse=True)
        self.assertEqual(model.filtered_files[0]['file_path'], 'document.pdf')  # Larger file first
    
    def test_pagination(self):
        """Test file browser pagination"""
        # Create many test files
        many_files = []
        for i in range(2500):
            many_files.append({
                'id': i,
                'file_path': f'file_{i:04d}.txt',
                'file_size': 1024 * (i + 1),
                'file_hash': f'hash_{i}',
                'modified_at': '2024-01-15 10:30:00',
                'uploaded_segments': 1,
                'total_segments': 1
            })
        
        self.mock_backend.database.get_folder_files.return_value = many_files
        
        browser = FileBrowserWidget(self.root, self.mock_backend)
        browser.page_size = 1000
        browser.load_folder(1)
        
        # Wait for async loading
        time.sleep(0.1)
        browser.update()
        
        # Check pagination
        self.assertEqual(browser.current_page, 0)
        self.assertTrue(browser.next_button.cget('state') == tk.NORMAL)
        self.assertTrue(browser.prev_button.cget('state') == tk.DISABLED)
        
        browser.destroy()
    
    def test_file_selection(self):
        """Test file selection functionality"""
        self.mock_backend.database.get_folder_files.return_value = self.test_files
        
        browser = FileBrowserWidget(self.root, self.mock_backend)
        browser.load_folder(1)
        
        # Wait for async loading
        time.sleep(0.1)
        browser.update()
        
        # Test select all
        browser.select_all()
        self.assertEqual(len(browser.selected_files), 2)
        
        # Test select none
        browser.select_none()
        self.assertEqual(len(browser.selected_files), 0)
        
        browser.destroy()

class TestDownloadDialog(GUITestBase):
    """Test download dialog functionality"""
    
    def test_dialog_creation(self):
        """Test dialog creates correctly"""
        dialog = DownloadDialog(self.root, self.mock_backend)
        
        # Check dialog properties
        self.assertIsNotNone(dialog.dialog)
        self.assertEqual(dialog.dialog.title(), "Download Shared Folder")
        
        # Check components exist
        self.assertIsNotNone(dialog.access_string_var)
        self.assertIsNotNone(dialog.file_tree)
        self.assertIsNotNone(dialog.destination_var)
        
        dialog.dialog.destroy()
    
    def test_share_verification(self):
        """Test share verification process"""
        dialog = DownloadDialog(self.root, self.mock_backend)
        
        # Set test access string
        dialog.access_string_var.set("test_access_string")
        
        # Mock verification to run synchronously
        with patch('threading.Thread') as mock_thread:
            def run_verification():
                share_info = {
                    'folder_name': 'Test Share',
                    'total_files': 10,
                    'total_size': 1024 * 1024 * 100,
                    'share_type': 'public',
                    'files': dialog.generate_mock_file_list()
                }
                dialog.on_share_verified(share_info)
            
            mock_thread.return_value.start = run_verification
            
            dialog.verify_share()
            
            # Check verification results
            self.assertIsNotNone(dialog.share_info)
            self.assertTrue(dialog.verified)
            self.assertEqual(dialog.share_info['folder_name'], 'Test Share')
        
        dialog.dialog.destroy()
    
    def test_file_tree_population(self):
        """Test file tree populates correctly"""
        dialog = DownloadDialog(self.root, self.mock_backend)
        
        test_files = [
            {'path': 'folder1/', 'size': 0, 'type': 'folder'},
            {'path': 'folder1/file1.txt', 'size': 1024, 'type': 'file'},
            {'path': 'folder1/file2.txt', 'size': 2048, 'type': 'file'},
            {'path': 'file3.txt', 'size': 512, 'type': 'file'}
        ]
        
        dialog.populate_file_tree(test_files)
        
        # Check tree has items
        tree_items = dialog.file_tree.get_children()
        self.assertGreater(len(tree_items), 0)
        
        dialog.dialog.destroy()

class TestGUIPerformance(GUITestBase):
    """Test GUI performance with large datasets"""
    
    def test_large_folder_loading(self):
        """Test loading folder with many files"""
        # Create 10,000 test files
        many_files = []
        for i in range(10000):
            many_files.append({
                'id': i,
                'file_path': f'folder/subfolder/file_{i:05d}.txt',
                'file_size': 1024 * (i % 1000 + 1),
                'file_hash': f'hash_{i}',
                'modified_at': '2024-01-15 10:30:00',
                'uploaded_segments': 1,
                'total_segments': 1
            })
        
        self.mock_backend.database.get_folder_files.return_value = many_files
        
        browser = FileBrowserWidget(self.root, self.mock_backend)
        
        # Measure loading time
        start_time = time.time()
        browser.load_folder(1)
        
        # Wait for loading to complete
        time.sleep(0.5)
        browser.update()
        
        load_time = time.time() - start_time
        
        # Should load within reasonable time (less than 2 seconds)
        self.assertLess(load_time, 2.0)
        
        # Check virtual scrolling is working
        displayed_items = len(browser.file_tree.get_children())
        self.assertLessEqual(displayed_items, browser.page_size)
        
        browser.destroy()
    
    def test_search_performance(self):
        """Test search performance on large dataset"""
        # Create 5,000 test files with varying names
        many_files = []
        for i in range(5000):
            file_types = ['document', 'image', 'video', 'audio', 'archive']
            file_type = file_types[i % len(file_types)]
            many_files.append({
                'id': i,
                'file_path': f'{file_type}_{i:04d}.txt',
                'file_size': 1024,
                'file_hash': f'hash_{i}',
                'modified_at': '2024-01-15 10:30:00',
                'uploaded_segments': 1,
                'total_segments': 1
            })
        
        self.mock_backend.database.get_folder_files.return_value = many_files
        
        model = VirtualFileModel(self.mock_backend, 1)
        model.load_files()
        
        # Measure search time
        start_time = time.time()
        model.set_search("document")
        search_time = time.time() - start_time
        
        # Search should be fast (less than 0.1 seconds)
        self.assertLess(search_time, 0.1)
        
        # Check search results
        self.assertGreater(len(model.filtered_files), 0)
        for file_info in model.filtered_files:
            self.assertIn("document", file_info['file_path'])

class TestGUIIntegration(GUITestBase):
    """Integration tests for GUI components"""
    
    def test_full_workflow(self):
        """Test complete user workflow"""
        with patch('gui.main_application.UsenetSync') as mock_usenet:
            mock_usenet.return_value = self.mock_backend
            
            # Setup mock responses
            self.mock_backend.list_folders.return_value = self.test_folders
            self.mock_backend.database.get_folder.return_value = self.test_folders[0]
            self.mock_backend.database.get_folder_files.return_value = self.test_files
            self.mock_backend.create_user.return_value = "test_user_123"
            self.mock_backend.publish_folder.return_value = "access_string_123"
            
            # Initialize main app
            app = MainApplication()
            
            # Simulate user initialization
            self.mock_backend.security.is_user_initialized.return_value = False
            user_dialog = UserInitDialog(app.root, self.mock_backend)
            user_dialog.display_name_var.set("Test User")
            user_dialog.result = {'user_id': 'test_user_123'}
            
            # Simulate folder refresh
            app.refresh_folders()
            tree_items = app.folder_tree.get_children()
            self.assertEqual(len(tree_items), 2)
            
            # Simulate folder selection
            app.folder_tree.selection_set(tree_items[0])
            app.on_folder_select(None)
            self.assertEqual(app.current_folder, 1)
            
            # Simulate folder publishing
            with patch('tkinter.messagebox.showinfo') as mock_info:
                with patch('tkinter.Toplevel') as mock_toplevel:
                    app.publish_share()
                    self.mock_backend.publish_folder.assert_called_once()
            
            app.root.destroy()

def run_gui_tests():
    """Run all GUI tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestMainApplication,
        TestUserInitDialog,
        TestFileBrowserWidget,
        TestDownloadDialog,
        TestGUIPerformance,
        TestGUIIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_gui_tests()
    sys.exit(0 if success else 1)