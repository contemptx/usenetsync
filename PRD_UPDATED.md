# Product Requirements Document (PRD) - UsenetSync
**Version 2.0 - Updated November 2024**

## 1. Executive Summary

### Product Vision
UsenetSync is a secure, high-performance file synchronization and sharing platform that leverages Usenet infrastructure for distributed storage while maintaining complete privacy through client-side encryption and obfuscation.

### Key Value Propositions
- **Privacy First**: Zero-knowledge architecture with client-side encryption
- **Massive Scale**: Handle 20TB+ datasets with millions of files
- **High Performance**: 100+ MB/s transfer speeds with parallel processing
- **Simple Sharing**: Share entire folder structures with a single ID
- **Cross-Platform**: Windows, macOS, Linux support via Tauri

### Target Market
- Privacy-conscious users needing secure file sharing
- Content creators requiring large file distribution
- Organizations needing decentralized backup solutions
- Power users with existing Usenet subscriptions

## 2. Core Features

### 2.1 File Management
- **Folder Indexing**: Index entire directory structures preserving hierarchy
- **Smart Segmentation**: Automatic file splitting (750KB segments)
- **Small File Packing**: Combine small files into single segments for efficiency
- **Version Control**: Track file changes and maintain version history
- **Selective Sync**: Choose specific files/folders to upload/download

### 2.2 Security & Privacy
- **End-to-End Encryption**: AES-256-GCM for all data
- **Obfuscated Storage**: Random message IDs and subjects on Usenet
- **Zero-Knowledge**: Server never sees decrypted data
- **Share Types**:
  - Public: No authentication required
  - Private: User ID verification (zero-knowledge proof)
  - Protected: Password-based access
- **Device Locking**: License tied to hardware fingerprint

### 2.3 Performance
- **Parallel Processing**: Multi-threaded upload/download
- **Connection Pooling**: Up to 30 concurrent NNTP connections
- **Memory-Mapped I/O**: 10x faster file operations
- **Bulk Database Ops**: 100x faster with PostgreSQL COPY
- **Resume Capability**: Segment-level resume for all operations
- **Progress Persistence**: Continue after app restart

### 2.4 User Experience
- **Simple Share IDs**: 24-character Base32 strings (e.g., MRFE3BX25XTF5CH6FPP2PXDL)
- **Folder Preview**: View complete structure before downloading
- **Selective Download**: Choose specific files from shares
- **Real-Time Progress**: Detailed progress for all operations
- **Bandwidth Control**: Configurable upload/download limits

## 3. Technical Architecture

### 3.1 Technology Stack
- **Backend**: Python 3.13 with async/await
- **Database**: PostgreSQL 16 with sharding
- **Frontend**: Tauri 2.0 + React 18 + TypeScript
- **State Management**: Zustand + TanStack Query
- **Styling**: Tailwind CSS + Radix UI
- **Build System**: Vite + Rust cargo

### 3.2 System Components
```
┌─────────────────────────────────────────────────┐
│                 Tauri Frontend                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │  React   │ │  Zustand │ │  WebAssembly │   │
│  │    UI    │ │   State  │ │   Workers    │   │
│  └──────────┘ └──────────┘ └──────────────┘   │
└─────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────┐
│              Rust Backend (Tauri)               │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │  License │ │  Device  │ │   File I/O   │   │
│  │   Check  │ │ Fingerpr │ │   Memory Map │   │
│  └──────────┘ └──────────┘ └──────────────┘   │
└─────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────┐
│              Python Core Engine                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │Encryption│ │   NNTP   │ │   Database   │   │
│  │  System  │ │  Client  │ │   Manager    │   │
│  └──────────┘ └──────────┘ └──────────────┘   │
└─────────────────────────────────────────────────┘
                        ↕
┌─────────────────────────────────────────────────┐
│           External Services                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │  Usenet  │ │PostgreSQL│ │License Server│   │
│  │  Servers │ │ Database │ │   (FastAPI)  │   │
│  └──────────┘ └──────────┘ └──────────────┘   │
└─────────────────────────────────────────────────┘
```

## 4. User Interface Requirements

### 4.1 Main Application Views

#### Dashboard
- System status overview
- Recent shares (created/accessed)
- Storage usage statistics
- Quick actions toolbar

#### File Browser
- Dual-pane interface (local/remote)
- Tree view for folders
- List/grid view for files
- Drag-and-drop support
- Context menus for operations

#### Upload Manager
- File/folder selection
- Segmentation preview
- Encryption settings
- Share type selection
- Progress tracking

#### Download Manager
- Share ID input
- Folder structure preview
- Selective file selection
- Download location picker
- Progress tracking with pause/resume

#### Share Manager
- List of created shares
- Share details and metadata
- Access logs and statistics
- Share editing and deletion
- QR code generation

#### Settings
- Usenet server configuration
- Performance tuning
- Security preferences
- License management
- Auto-update settings

### 4.2 UI Components Needed

#### Core Components
- `AppShell` - Main application layout
- `NavigationSidebar` - Side navigation menu
- `HeaderBar` - Top bar with search and user menu
- `StatusBar` - Bottom status indicator

#### File Management
- `FileExplorer` - File browsing interface
- `FileTree` - Hierarchical folder view
- `FileList` - File listing with sorting
- `FilePreview` - Quick file preview
- `FileUploader` - Drag-drop upload zone

#### Share Components
- `ShareCreator` - Create new shares wizard
- `ShareViewer` - View share contents
- `ShareList` - List of shares with filters
- `ShareDetails` - Detailed share information
- `ShareAccessLog` - Access history

#### Progress Components
- `ProgressBar` - Visual progress indicator
- `ProgressList` - Multiple operation tracking
- `TransferSpeed` - Speed indicators
- `SegmentProgress` - Segment-level detail

#### Dialogs
- `LicenseActivation` - License key entry
- `ServerConfig` - Usenet server setup
- `PasswordPrompt` - Protected share access
- `ConfirmDialog` - Action confirmations
- `ErrorDialog` - Error display with details

## 5. Performance Requirements

### 5.1 Benchmarks
- **Upload Speed**: ≥100 MB/s with 30 connections
- **Download Speed**: ≥100 MB/s with 30 connections
- **Database Operations**: 
  - Insert 100K segments < 10 seconds
  - Query 1M records < 1 second
- **Memory Usage**: < 500MB for 1M file index
- **Startup Time**: < 3 seconds
- **UI Responsiveness**: < 100ms for all interactions

### 5.2 Scalability
- Support 20TB total data
- Handle 300,000 folders
- Manage 3,000,000 files
- Process 30,000,000 segments
- Concurrent users: 1 (per license)

## 6. Security Requirements

### 6.1 Encryption
- **Algorithm**: AES-256-GCM
- **Key Derivation**: Scrypt for passwords
- **Random Generation**: Cryptographically secure
- **Zero-Knowledge Proofs**: Schnorr-based for private shares

### 6.2 Authentication
- **License Key**: UUID-based with checksum
- **Device Lock**: CPU + MAC + Disk fingerprint
- **Offline Mode**: 30-day grace period
- **Anti-Tampering**: Binary integrity checks

### 6.3 Privacy
- **No Telemetry**: No usage tracking without consent
- **Local First**: All processing client-side
- **Obfuscation**: No identifiable patterns in storage
- **Secure Delete**: Overwrite sensitive data

## 7. Monetization

### 7.1 Pricing Model
- **Annual Subscription**: $29.99/year
- **Features**: All features included
- **Support**: Email support included
- **Updates**: Automatic updates included

### 7.2 License Management
- One license per device
- Non-transferable
- Auto-renewal available
- Volume discounts for organizations

## 8. Development Phases

### Phase 1: Core Completion ✅
- Backend architecture
- Security implementation
- Database integration
- NNTP operations
- Performance optimizations

### Phase 2: Frontend Development (Current)
- Tauri application setup
- React component library
- State management
- API integration
- UI/UX polish

### Phase 3: License System
- License server deployment
- Payment integration
- Activation flow
- Renewal management

### Phase 4: Testing & Launch
- Beta testing program
- Performance validation
- Security audit
- Documentation
- Marketing website

## 9. Success Metrics

### 9.1 Technical KPIs
- 99.9% uptime for license server
- < 1% error rate for operations
- 100+ MB/s average transfer speed
- < 500ms UI response time

### 9.2 Business KPIs
- 1,000 paid users in Year 1
- 80% annual renewal rate
- < 5% refund rate
- 4.5+ star average rating

### 9.3 User Satisfaction
- Net Promoter Score > 50
- Support ticket resolution < 24 hours
- Feature request implementation cycle < 30 days

## 10. Risk Mitigation

### 10.1 Technical Risks
- **Usenet Server Changes**: Abstract NNTP layer for flexibility
- **Database Scaling**: Implement sharding from start
- **Performance Degradation**: Continuous monitoring and optimization

### 10.2 Business Risks
- **Competition**: Focus on privacy and ease-of-use differentiators
- **Piracy**: Strong device-locking and license validation
- **Support Burden**: Comprehensive documentation and self-service

### 10.3 Legal Risks
- **Copyright**: Clear terms of service
- **Privacy Laws**: GDPR compliance built-in
- **Export Controls**: Encryption compliance

## 11. Timeline

### Q4 2024
- Week 1-2: Tauri app and React components
- Week 3: License system implementation
- Week 4: Integration testing

### Q1 2025
- Month 1: Beta testing program
- Month 2: Bug fixes and optimization
- Month 3: Public launch

## 12. Appendices

### A. Competitor Analysis
- **Comparison with cloud storage** (Dropbox, Google Drive)
- **Comparison with P2P** (BitTorrent, IPFS)
- **Comparison with Usenet tools** (SABnzbd, NZBGet)

### B. Technical Specifications
- Detailed API documentation
- Database schema
- Encryption specifications
- Network protocols

### C. User Research
- Survey results from potential users
- Feature prioritization matrix
- Usability testing feedback