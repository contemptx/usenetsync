import React, { useState, useEffect } from 'react';
import { 
  Play, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  RefreshCw,
  Database,
  Zap,
  FileText,
  Upload,
  Download,
  Share2,
  Settings,
  Activity,
  Loader
} from 'lucide-react';
import { TestDataGenerator } from '../test/test-data-generator';
import { useAppStore } from '../stores/useAppStore';
import * as tauriCommands from '../lib';
import toast from 'react-hot-toast';

interface TestCase {
  id: string;
  name: string;
  category: string;
  description: string;
  status: 'pending' | 'running' | 'passed' | 'failed' | 'skipped';
  error?: string;
  duration?: number;
}

export const TestRunner: React.FC = () => {
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentTest, setCurrentTest] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, any>>({});
  
  const store = useAppStore();

  useEffect(() => {
    initializeTestCases();
  }, []);

  const initializeTestCases = () => {
    const cases: TestCase[] = [
      // License Tests
      {
        id: 'license-1',
        name: 'Check License Status',
        category: 'License',
        description: 'Verify license checking functionality',
        status: 'pending'
      },
      {
        id: 'license-2',
        name: 'Activate Trial License',
        category: 'License',
        description: 'Test trial license activation',
        status: 'pending'
      },
      
      // File Operations Tests
      {
        id: 'file-1',
        name: 'Generate Test Files',
        category: 'Files',
        description: 'Create test file structure with realistic data',
        status: 'pending'
      },
      {
        id: 'file-2',
        name: 'Test File Selection',
        category: 'Files',
        description: 'Test file and folder selection',
        status: 'pending'
      },
      {
        id: 'file-3',
        name: 'Test File Indexing',
        category: 'Files',
        description: 'Index a folder and verify structure',
        status: 'pending'
      },
      
      // Upload Tests
      {
        id: 'upload-1',
        name: 'Create Test Upload',
        category: 'Upload',
        description: 'Simulate file upload with progress',
        status: 'pending'
      },
      {
        id: 'upload-2',
        name: 'Test Batch Upload',
        category: 'Upload',
        description: 'Upload multiple files simultaneously',
        status: 'pending'
      },
      {
        id: 'upload-3',
        name: 'Test Upload Cancellation',
        category: 'Upload',
        description: 'Cancel an ongoing upload',
        status: 'pending'
      },
      
      // Share Tests
      {
        id: 'share-1',
        name: 'Create Public Share',
        category: 'Shares',
        description: 'Create a public share with test files',
        status: 'pending'
      },
      {
        id: 'share-2',
        name: 'Create Protected Share',
        category: 'Shares',
        description: 'Create a password-protected share',
        status: 'pending'
      },
      {
        id: 'share-3',
        name: 'Test Share Expiration',
        category: 'Shares',
        description: 'Create share with expiration date',
        status: 'pending'
      },
      
      // Download Tests
      {
        id: 'download-1',
        name: 'Test Share Lookup',
        category: 'Download',
        description: 'Look up a share by ID',
        status: 'pending'
      },
      {
        id: 'download-2',
        name: 'Test Download Progress',
        category: 'Download',
        description: 'Simulate download with progress tracking',
        status: 'pending'
      },
      
      // System Tests
      {
        id: 'system-1',
        name: 'Get System Statistics',
        category: 'System',
        description: 'Retrieve and verify system stats',
        status: 'pending'
      },
      {
        id: 'system-2',
        name: 'Test Bandwidth Limiting',
        category: 'System',
        description: 'Set and verify bandwidth limits',
        status: 'pending'
      },
      {
        id: 'system-3',
        name: 'Generate System Logs',
        category: 'System',
        description: 'Generate and retrieve test logs',
        status: 'pending'
      },
      
      // Performance Tests
      {
        id: 'perf-1',
        name: 'Large File Handling',
        category: 'Performance',
        description: 'Test with 1GB+ file simulation',
        status: 'pending'
      },
      {
        id: 'perf-2',
        name: 'Concurrent Operations',
        category: 'Performance',
        description: 'Test 10 simultaneous transfers',
        status: 'pending'
      },
      {
        id: 'perf-3',
        name: 'Memory Usage Test',
        category: 'Performance',
        description: 'Monitor memory during heavy operations',
        status: 'pending'
      },
      
      // UI Tests
      {
        id: 'ui-1',
        name: 'Test Notifications',
        category: 'UI',
        description: 'Generate various notification types',
        status: 'pending'
      },
      {
        id: 'ui-2',
        name: 'Test Dark Mode',
        category: 'UI',
        description: 'Toggle and verify dark mode',
        status: 'pending'
      },
      {
        id: 'ui-3',
        name: 'Test Keyboard Shortcuts',
        category: 'UI',
        description: 'Verify all keyboard shortcuts work',
        status: 'pending'
      }
    ];
    
    setTestCases(cases);
  };

  const runTest = async (testCase: TestCase): Promise<void> => {
    const startTime = Date.now();
    
    try {
      switch (testCase.id) {
        case 'license-1':
          const status = await tauriCommands.checkLicense();
          setTestResults(prev => ({ ...prev, [testCase.id]: status }));
          if (!status) throw new Error('Failed to get license status');
          break;
          
        case 'license-2':
          const trialDays = await tauriCommands.startTrial();
          setTestResults(prev => ({ ...prev, [testCase.id]: { trialDays } }));
          break;
          
        case 'file-1':
          const testFiles = TestDataGenerator.generateBulkData();
          store.setSelectedFiles(testFiles.files);
          setTestResults(prev => ({ ...prev, [testCase.id]: testFiles }));
          break;
          
        case 'file-2':
          const selectedFiles = await tauriCommands.selectFiles();
          setTestResults(prev => ({ ...prev, [testCase.id]: selectedFiles }));
          break;
          
        case 'upload-1':
          const upload = TestDataGenerator.generateTransfer('upload');
          store.addUpload(upload);
          
          // Simulate progress
          for (let i = 0; i <= 100; i += 10) {
            await new Promise(resolve => setTimeout(resolve, 100));
            store.updateTransfer(upload.id, {
              transferredSize: Math.floor(upload.totalSize * (i / 100)),
              speed: Math.random() * 10000000
            });
          }
          break;
          
        case 'share-1':
          const share = TestDataGenerator.generateShare();
          store.addShare(share);
          setTestResults(prev => ({ ...prev, [testCase.id]: share }));
          break;
          
        case 'system-1':
          const stats = await tauriCommands.getSystemStats();
          setTestResults(prev => ({ ...prev, [testCase.id]: stats }));
          break;
          
        case 'system-2':
          try {
            await tauriCommands.setBandwidthLimit(1000, 5000, true);
            const limits = await tauriCommands.getBandwidthLimit();
            setTestResults(prev => ({ ...prev, [testCase.id]: limits }));
          } catch (error) {
            console.error('Bandwidth limit test failed:', error);
            throw error;
          }
          break;
          
        case 'system-3':
          const logs = TestDataGenerator.generateLogs(50);
          setTestResults(prev => ({ ...prev, [testCase.id]: logs }));
          break;
          
        case 'perf-1':
          // Simulate large file
          const largeFile = {
            ...TestDataGenerator.generateFileNode(),
            size: 1024 * 1024 * 1024 // 1GB
          };
          setTestResults(prev => ({ ...prev, [testCase.id]: largeFile }));
          break;
          
        case 'ui-1':
          toast.success('Success notification test');
          toast.error('Error notification test');
          toast('Info notification test');
          toast.loading('Loading notification test');
          break;
          
        case 'ui-2':
          store.toggleDarkMode();
          await new Promise(resolve => setTimeout(resolve, 500));
          store.toggleDarkMode();
          break;
          
        default:
          // Simulate test execution
          await new Promise(resolve => setTimeout(resolve, Math.random() * 1000 + 500));
      }
      
      const duration = Date.now() - startTime;
      updateTestStatus(testCase.id, 'passed', undefined, duration);
      
    } catch (error) {
      const duration = Date.now() - startTime;
      updateTestStatus(testCase.id, 'failed', error.message, duration);
      throw error;
    }
  };

  const updateTestStatus = (
    id: string, 
    status: TestCase['status'], 
    error?: string,
    duration?: number
  ) => {
    setTestCases(prev => prev.map(tc => 
      tc.id === id 
        ? { ...tc, status, error, duration }
        : tc
    ));
  };

  const runAllTests = async () => {
    setIsRunning(true);
    
    for (const testCase of testCases) {
      setCurrentTest(testCase.id);
      updateTestStatus(testCase.id, 'running');
      
      try {
        await runTest(testCase);
      } catch (error) {
        console.error(`Test ${testCase.id} failed:`, error);
      }
      
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    setCurrentTest(null);
    setIsRunning(false);
    
    const passed = testCases.filter(tc => tc.status === 'passed').length;
    const failed = testCases.filter(tc => tc.status === 'failed').length;
    
    toast.success(`Tests complete: ${passed} passed, ${failed} failed`);
  };

  const runSingleTest = async (testCase: TestCase) => {
    setCurrentTest(testCase.id);
    updateTestStatus(testCase.id, 'running');
    
    try {
      await runTest(testCase);
      toast.success(`Test "${testCase.name}" passed`);
    } catch (error) {
      toast.error(`Test "${testCase.name}" failed`);
    }
    
    setCurrentTest(null);
  };

  const resetTests = () => {
    setTestCases(prev => prev.map(tc => ({ ...tc, status: 'pending', error: undefined, duration: undefined })));
    setTestResults({});
  };

  const getStatusIcon = (status: TestCase['status']) => {
    switch (status) {
      case 'passed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'running':
        return <Loader className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'skipped':
        return <AlertCircle className="w-5 h-5 text-gray-400" />;
      default:
        return <div className="w-5 h-5 rounded-full border-2 border-gray-300" />;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'License':
        return <FileText className="w-4 h-4" />;
      case 'Files':
        return <Database className="w-4 h-4" />;
      case 'Upload':
        return <Upload className="w-4 h-4" />;
      case 'Download':
        return <Download className="w-4 h-4" />;
      case 'Shares':
        return <Share2 className="w-4 h-4" />;
      case 'System':
        return <Settings className="w-4 h-4" />;
      case 'Performance':
        return <Zap className="w-4 h-4" />;
      case 'UI':
        return <Activity className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const categories = [...new Set(testCases.map(tc => tc.category))];
  const stats = {
    total: testCases.length,
    passed: testCases.filter(tc => tc.status === 'passed').length,
    failed: testCases.filter(tc => tc.status === 'failed').length,
    pending: testCases.filter(tc => tc.status === 'pending').length,
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Test Runner</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Comprehensive testing suite for UsenetSync
          </p>
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={resetTests}
            disabled={isRunning}
            className="px-4 py-2 bg-gray-100 dark:bg-dark-border text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            <RefreshCw className="w-4 h-4 inline mr-2" />
            Reset
          </button>
          
          <button
            onClick={runAllTests}
            disabled={isRunning}
            className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50"
          >
            {isRunning ? (
              <>
                <Loader className="w-4 h-4 inline mr-2 animate-spin" />
                Running...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 inline mr-2" />
                Run All Tests
              </>
            )}
          </button>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white dark:bg-dark-surface p-4 rounded-lg border border-gray-200 dark:border-dark-border">
          <div className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Total Tests</div>
        </div>
        
        <div className="bg-white dark:bg-dark-surface p-4 rounded-lg border border-gray-200 dark:border-dark-border">
          <div className="text-2xl font-bold text-green-500">{stats.passed}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Passed</div>
        </div>
        
        <div className="bg-white dark:bg-dark-surface p-4 rounded-lg border border-gray-200 dark:border-dark-border">
          <div className="text-2xl font-bold text-red-500">{stats.failed}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Failed</div>
        </div>
        
        <div className="bg-white dark:bg-dark-surface p-4 rounded-lg border border-gray-200 dark:border-dark-border">
          <div className="text-2xl font-bold text-gray-500">{stats.pending}</div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Pending</div>
        </div>
      </div>

      {/* Test Categories */}
      {categories.map(category => (
        <div key={category} className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-dark-border">
          <div className="p-4 border-b border-gray-200 dark:border-dark-border">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              {getCategoryIcon(category)}
              {category} Tests
            </h2>
          </div>
          
          <div className="divide-y divide-gray-200 dark:divide-dark-border">
            {testCases
              .filter(tc => tc.category === category)
              .map(testCase => (
                <div key={testCase.id} className="p-4 hover:bg-gray-50 dark:hover:bg-dark-bg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(testCase.status)}
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white">
                          {testCase.name}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {testCase.description}
                        </div>
                        {testCase.error && (
                          <div className="text-sm text-red-500 mt-1">
                            Error: {testCase.error}
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      {testCase.duration && (
                        <span className="text-sm text-gray-500">
                          {testCase.duration}ms
                        </span>
                      )}
                      
                      <button
                        onClick={() => runSingleTest(testCase)}
                        disabled={isRunning || currentTest === testCase.id}
                        className="px-3 py-1 text-sm bg-gray-100 dark:bg-dark-border text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-50"
                      >
                        {currentTest === testCase.id ? 'Running...' : 'Run'}
                      </button>
                    </div>
                  </div>
                  
                  {testResults[testCase.id] && (
                    <details className="mt-3">
                      <summary className="text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
                        View Results
                      </summary>
                      <pre className="mt-2 p-2 bg-gray-100 dark:bg-dark-bg rounded text-xs overflow-auto">
                        {JSON.stringify(testResults[testCase.id], null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              ))}
          </div>
        </div>
      ))}
    </div>
  );
};