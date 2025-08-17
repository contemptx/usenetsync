import { FileNode, Share, Transfer, LicenseStatus } from '../types';
import { faker } from '@faker-js/faker';

export class TestDataGenerator {
  static generateFileNode(depth = 0, maxDepth = 3): FileNode {
    const isFolder = depth < maxDepth && Math.random() > 0.5;
    const node: FileNode = {
      id: faker.string.uuid(),
      name: isFolder ? faker.system.directoryPath() : faker.system.fileName(),
      type: isFolder ? 'folder' : 'file',
      size: isFolder ? 0 : faker.number.int({ min: 1024, max: 1024 * 1024 * 100 }),
      path: faker.system.filePath(),
      modifiedAt: faker.date.recent(),
      selected: false,
    };

    if (isFolder && depth < maxDepth) {
      const childCount = faker.number.int({ min: 1, max: 5 });
      node.children = Array.from({ length: childCount }, () => 
        this.generateFileNode(depth + 1, maxDepth)
      );
      node.size = node.children.reduce((sum, child) => sum + child.size, 0);
    }

    return node;
  }

  static generateShare(): Share {
    return {
      id: faker.string.uuid(),
      shareId: faker.string.alphanumeric(12).toUpperCase(),
      type: faker.helpers.arrayElement(['public', 'private', 'protected']),
      name: faker.system.fileName(),
      size: faker.number.int({ min: 1024 * 1024, max: 1024 * 1024 * 1024 }),
      fileCount: faker.number.int({ min: 1, max: 100 }),
      folderCount: faker.number.int({ min: 0, max: 20 }),
      createdAt: faker.date.recent(),
      expiresAt: Math.random() > 0.5 ? faker.date.future() : undefined,
      accessCount: faker.number.int({ min: 0, max: 1000 }),
      lastAccessed: faker.date.recent(),
    };
  }

  static generateTransfer(type: 'upload' | 'download'): Transfer {
    const totalSize = faker.number.int({ min: 1024 * 1024, max: 1024 * 1024 * 1024 });
    const progress = faker.number.float({ min: 0, max: 1 });
    
    return {
      id: faker.string.uuid(),
      type,
      name: faker.system.fileName(),
      totalSize,
      transferredSize: Math.floor(totalSize * progress),
      speed: faker.number.int({ min: 100000, max: 10000000 }),
      eta: faker.number.int({ min: 0, max: 3600 }),
      status: faker.helpers.arrayElement(['active', 'paused', 'completed', 'error']),
      segments: Array.from({ length: faker.number.int({ min: 1, max: 10 }) }, (_, i) => ({
        index: i,
        size: Math.floor(totalSize / 10),
        completed: Math.random() > 0.3,
        messageId: faker.string.uuid(),
        retries: faker.number.int({ min: 0, max: 3 }),
      })),
      startedAt: faker.date.recent(),
      completedAt: progress === 1 ? faker.date.recent() : undefined,
      error: undefined,
    };
  }

  static generateLicenseStatus(): LicenseStatus {
    const activated = Math.random() > 0.2;
    return {
      activated,
      genuine: activated,
      trial: !activated,
      trialDays: !activated ? faker.number.int({ min: 1, max: 30 }) : undefined,
      hardwareId: faker.string.alphanumeric(16).toUpperCase(),
      tier: faker.helpers.arrayElement(['basic', 'pro', 'enterprise']),
      features: {
        maxFileSize: faker.number.int({ min: 1024 * 1024 * 100, max: 1024 * 1024 * 1024 * 10 }),
        maxConnections: faker.number.int({ min: 10, max: 100 }),
        maxShares: faker.number.int({ min: 10, max: 1000 }),
      },
    };
  }

  static generateBulkData() {
    return {
      files: Array.from({ length: 10 }, () => this.generateFileNode()),
      shares: Array.from({ length: 5 }, () => this.generateShare()),
      uploads: Array.from({ length: 3 }, () => this.generateTransfer('upload')),
      downloads: Array.from({ length: 3 }, () => this.generateTransfer('download')),
      license: this.generateLicenseStatus(),
    };
  }

  static generateSystemStats() {
    return {
      cpuUsage: faker.number.float({ min: 0, max: 100 }),
      memoryUsage: faker.number.float({ min: 0, max: 100 }),
      diskUsage: faker.number.float({ min: 0, max: 100 }),
      networkSpeed: {
        upload: faker.number.int({ min: 0, max: 10000000 }),
        download: faker.number.int({ min: 0, max: 10000000 }),
      },
      activeTransfers: faker.number.int({ min: 0, max: 10 }),
      totalShares: faker.number.int({ min: 0, max: 100 }),
    };
  }

  static generateLogs(count = 100) {
    return Array.from({ length: count }, (_, i) => ({
      id: faker.string.uuid(),
      timestamp: faker.date.recent(),
      level: faker.helpers.arrayElement(['debug', 'info', 'warning', 'error', 'critical']),
      category: faker.helpers.arrayElement(['system', 'network', 'security', 'database', 'ui']),
      message: faker.lorem.sentence(),
      details: Math.random() > 0.5 ? { 
        extra: faker.lorem.paragraph(),
        code: faker.number.int({ min: 100, max: 999 })
      } : undefined,
      source: faker.helpers.arrayElement(['backend', 'frontend', 'tauri']),
    }));
  }
}