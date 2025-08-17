// Core Types for UsenetSync

export interface User {
  id: string;
  email: string;
  username: string;
  tier: 'basic' | 'pro' | 'enterprise';
  licenseValid: boolean;
  hardwareId: string;
}

export interface Share {
  id: string;
  shareId: string;
  type: 'public' | 'private' | 'protected';
  name: string;
  size: number;
  fileCount: number;
  folderCount: number;
  createdAt: Date;
  expiresAt?: Date;
  accessCount: number;
  lastAccessed?: Date;
}

export interface FileNode {
  id: string;
  name: string;
  type: 'file' | 'folder';
  size: number;
  path: string;
  children?: FileNode[];
  selected?: boolean;
  progress?: number;
  hash?: string;
  modifiedAt: Date;
}

export interface Transfer {
  id: string;
  type: 'upload' | 'download';
  name: string;
  totalSize: number;
  transferredSize: number;
  speed: number;
  eta: number;
  status: 'pending' | 'active' | 'paused' | 'completed' | 'error';
  segments: SegmentProgress[];
  startedAt: Date;
  completedAt?: Date;
  error?: string;
}

export interface SegmentProgress {
  index: number;
  size: number;
  completed: boolean;
  messageId?: string;
  retries: number;
}

export interface ServerConfig {
  hostname: string;
  port: number;
  username: string;
  password: string;
  useSsl: boolean;
  maxConnections: number;
  group: string;
}

export interface LicenseStatus {
  activated: boolean;
  genuine: boolean;
  trial: boolean;
  trialDays?: number;
  hardwareId: string;
  tier: string;
  features: {
    maxFileSize: number;
    maxConnections: number;
    maxShares: number;
  };
}

export interface SystemStats {
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  networkSpeed: {
    upload: number;
    download: number;
  };
  activeTransfers: number;
  totalShares: number;
}