import { describe, it, expect } from 'vitest';
import { TestDataGenerator } from '../test-data-generator';

describe('TestDataGenerator', () => {
  describe('generateFileNode', () => {
    it('should generate a valid file node', () => {
      const node = TestDataGenerator.generateFileNode();
      
      expect(node).toBeDefined();
      expect(node.id).toBeTruthy();
      expect(node.name).toBeTruthy();
      expect(node.type).toMatch(/^(file|folder)$/);
      expect(node.size).toBeGreaterThanOrEqual(0);
      expect(node.path).toBeTruthy();
      expect(node.modifiedAt).toBeInstanceOf(Date);
    });

    it('should generate nested structure when depth allows', () => {
      const node = TestDataGenerator.generateFileNode(0, 2);
      
      if (node.type === 'folder' && node.children) {
        expect(Array.isArray(node.children)).toBe(true);
        expect(node.children.length).toBeGreaterThanOrEqual(0);
      }
    });
  });

  describe('generateShare', () => {
    it('should generate a valid share', () => {
      const share = TestDataGenerator.generateShare();
      
      expect(share).toBeDefined();
      expect(share.id).toBeTruthy();
      expect(share.shareId).toMatch(/^[A-Z0-9]{12}$/);
      expect(share.type).toMatch(/^(public|private|protected)$/);
      expect(share.name).toBeTruthy();
      expect(share.size).toBeGreaterThan(0);
      expect(share.fileCount).toBeGreaterThanOrEqual(1);
      expect(share.createdAt).toBeInstanceOf(Date);
    });
  });

  describe('generateTransfer', () => {
    it('should generate a valid upload transfer', () => {
      const transfer = TestDataGenerator.generateTransfer('upload');
      
      expect(transfer).toBeDefined();
      expect(transfer.type).toBe('upload');
      expect(transfer.id).toBeTruthy();
      expect(transfer.name).toBeTruthy();
      expect(transfer.totalSize).toBeGreaterThan(0);
      expect(transfer.transferredSize).toBeGreaterThanOrEqual(0);
      expect(transfer.transferredSize).toBeLessThanOrEqual(transfer.totalSize);
      expect(transfer.status).toMatch(/^(active|paused|completed|error)$/);
    });

    it('should generate a valid download transfer', () => {
      const transfer = TestDataGenerator.generateTransfer('download');
      
      expect(transfer.type).toBe('download');
      expect(transfer.segments).toBeDefined();
      expect(Array.isArray(transfer.segments)).toBe(true);
    });
  });

  describe('generateLicenseStatus', () => {
    it('should generate a valid license status', () => {
      const license = TestDataGenerator.generateLicenseStatus();
      
      expect(license).toBeDefined();
      expect(typeof license.activated).toBe('boolean');
      expect(typeof license.genuine).toBe('boolean');
      expect(license.hardwareId).toMatch(/^[A-Z0-9]{16}$/);
      expect(license.tier).toMatch(/^(basic|pro|enterprise)$/);
      expect(license.features).toBeDefined();
      expect(license.features.maxFileSize).toBeGreaterThan(0);
      expect(license.features.maxConnections).toBeGreaterThan(0);
    });
  });

  describe('generateBulkData', () => {
    it('should generate complete bulk test data', () => {
      const data = TestDataGenerator.generateBulkData();
      
      expect(data).toBeDefined();
      expect(data.files).toHaveLength(10);
      expect(data.shares).toHaveLength(5);
      expect(data.uploads).toHaveLength(3);
      expect(data.downloads).toHaveLength(3);
      expect(data.license).toBeDefined();
      
      // Verify all uploads are upload type
      data.uploads.forEach(upload => {
        expect(upload.type).toBe('upload');
      });
      
      // Verify all downloads are download type
      data.downloads.forEach(download => {
        expect(download.type).toBe('download');
      });
    });
  });

  describe('generateSystemStats', () => {
    it('should generate valid system statistics', () => {
      const stats = TestDataGenerator.generateSystemStats();
      
      expect(stats).toBeDefined();
      expect(stats.cpuUsage).toBeGreaterThanOrEqual(0);
      expect(stats.cpuUsage).toBeLessThanOrEqual(100);
      expect(stats.memoryUsage).toBeGreaterThanOrEqual(0);
      expect(stats.memoryUsage).toBeLessThanOrEqual(100);
      expect(stats.diskUsage).toBeGreaterThanOrEqual(0);
      expect(stats.diskUsage).toBeLessThanOrEqual(100);
      expect(stats.networkSpeed).toBeDefined();
      expect(stats.networkSpeed.upload).toBeGreaterThanOrEqual(0);
      expect(stats.networkSpeed.download).toBeGreaterThanOrEqual(0);
    });
  });

  describe('generateLogs', () => {
    it('should generate the specified number of logs', () => {
      const count = 25;
      const logs = TestDataGenerator.generateLogs(count);
      
      expect(logs).toHaveLength(count);
    });

    it('should generate valid log entries', () => {
      const logs = TestDataGenerator.generateLogs(5);
      
      logs.forEach(log => {
        expect(log.id).toBeTruthy();
        expect(log.timestamp).toBeInstanceOf(Date);
        expect(log.level).toMatch(/^(debug|info|warning|error|critical)$/);
        expect(log.category).toMatch(/^(system|network|security|database|ui)$/);
        expect(log.message).toBeTruthy();
        expect(log.source).toMatch(/^(backend|frontend|tauri)$/);
      });
    });
  });
});