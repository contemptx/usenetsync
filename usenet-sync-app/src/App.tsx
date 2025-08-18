import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { useAppStore } from './stores/useAppStore';
import { checkLicense, onTransferProgress, onTransferComplete, onTransferError, onLicenseExpired, isUserInitialized, initializeUser } from './lib';

// Components
import { LicenseActivation } from './components/LicenseActivation';
import { AppShell } from './components/AppShell';

// Pages
import { Dashboard } from './pages/Dashboard';
import { Upload } from './pages/Upload';
import { Download } from './pages/Download';
import { Shares } from './pages/Shares';
import { FolderManagement } from './pages/FolderManagement';
import UserProfile from './pages/UserProfile';
import { Settings } from './pages/Settings';
import { Logs } from './pages/Logs';
import { TestRunner } from './pages/TestRunner';

// Create query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
    },
  },
});

function App() {
  const [isLicenseChecked, setIsLicenseChecked] = useState(false);
  const [isLicenseValid, setIsLicenseValid] = useState(false);
  const { setLicenseStatus, updateTransfer, darkMode } = useAppStore();

  // Apply dark mode class to document
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Check license and user initialization on startup
  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Check license first
        const status = await checkLicense();
        setLicenseStatus(status);
        setIsLicenseValid(status.activated && status.genuine);
        
        // Check if user is initialized (only if license is valid)
        if (status.activated && status.genuine) {
          try {
            const userInitialized = await isUserInitialized();
            if (!userInitialized) {
              // Auto-initialize user with default display name
              await initializeUser();
              console.log('User profile initialized automatically');
            }
          } catch (error) {
            console.error('Failed to check/initialize user:', error);
            // Non-critical error, continue
          }
        }
      } catch (error) {
        console.error('Failed to check license:', error);
        setIsLicenseValid(false);
      } finally {
        setIsLicenseChecked(true);
      }
    };

    initializeApp();
  }, [setLicenseStatus]);

  // Set up event listeners
  useEffect(() => {
    const unsubscribeProgress = onTransferProgress((progress) => {
      updateTransfer(progress.id, {
        transferredSize: progress.transferredSize,
        speed: progress.speed,
        eta: progress.eta,
        segments: progress.segments
      });
    });

    const unsubscribeComplete = onTransferComplete((transfer) => {
      updateTransfer(transfer.id, {
        status: 'completed',
        completedAt: new Date()
      });
    });

    const unsubscribeError = onTransferError((error) => {
      updateTransfer(error.transferId, {
        status: 'error',
        error: error.message
      });
    });

    const unsubscribeExpired = onLicenseExpired(() => {
      setIsLicenseValid(false);
      setLicenseStatus({
        activated: false,
        genuine: false,
        trial: false,
        hardwareId: '',
        tier: 'basic' as 'basic' | 'pro' | 'enterprise'
      });
    });

    return () => {
      unsubscribeProgress.then((fn: any) => fn());
      unsubscribeComplete.then((fn: any) => fn());
      unsubscribeError.then((fn: any) => fn());
      unsubscribeExpired.then((fn: any) => fn());
    };
  }, [updateTransfer, setLicenseStatus]);

  // Show loading while checking license
  if (!isLicenseChecked) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50 dark:bg-dark-bg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Checking license...</p>
        </div>
      </div>
    );
  }

  // Show license activation if not valid
  if (!isLicenseValid) {
    return (
      <div className="h-screen bg-gray-50 dark:bg-dark-bg">
        <LicenseActivation 
          onActivated={() => {
            setIsLicenseValid(true);
          }} 
        />
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="h-screen bg-gray-50 dark:bg-dark-bg">
          <Routes>
            <Route path="/" element={<AppShell />}>
              <Route index element={<Dashboard />} />
              <Route path="upload" element={<Upload />} />
              <Route path="download" element={<Download />} />
              <Route path="shares" element={<Shares />} />
              <Route path="folders" element={<FolderManagement />} />
              <Route path="profile" element={<UserProfile />} />
              <Route path="settings" element={<Settings />} />
              <Route path="logs" element={<Logs />} />
              <Route path="test" element={<TestRunner />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
          
          <Toaster
            position="bottom-right"
            toastOptions={{
              className: 'dark:bg-dark-surface dark:text-white',
              duration: 4000,
            }}
          />
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
