# USENET SYNC DEVELOPMENT RULES - NON-NEGOTIABLE

## ABSOLUTE BANS
- ❌ NEVER use placeholder data: "test", "example", "demo", "sample", "TODO", "FIXME"
- ❌ NEVER use mock implementations: Mock*, Fake*, Stub*, Test* classes
- ❌ NEVER use random data generation: random.uniform(), random.randint()
- ❌ NEVER use email addresses in Usenet context
- ❌ NEVER implement permission levels (read/write/admin) - Usenet is binary access
- ❌ NEVER return test data when system unavailable - raise proper exceptions
- ❌ NEVER use hardcoded paths like "/tmp/test" or "C:\\temp\\test"
- ❌ NEVER create files with "example" or "sample" in the name
- ❌ NEVER use placeholder IDs like "TEST-123" or "DEMO-456"

## REQUIRED REAL SYSTEMS
- ✅ ALWAYS use real NNTP server: news.newshosting.com:563 (SSL)
- ✅ ALWAYS use real database queries - no in-memory substitutes
- ✅ ALWAYS use real file system operations - no virtual files
- ✅ ALWAYS use real cryptographic operations - no simplified encryption
- ✅ ALWAYS measure real metrics - no simulated statistics
- ✅ ALWAYS connect to actual UnifiedSystem methods
- ✅ ALWAYS use real Message-IDs in format: <timestamp.random@domain>
- ✅ ALWAYS verify operations with actual database state

## USENET ONE-WAY RULES
- ✅ Message-IDs are CLIENT-GENERATED (never server-assigned)
- ✅ Posts are APPEND-ONLY (no edits, no deletes)
- ✅ Retries must be IDEMPOTENT (same Message-ID)
- ✅ Propagation is EVENTUAL (no guaranteed timing)
- ✅ Access is BINARY (have key or don't - no permissions)
- ✅ No user profiles - only user_id identifiers
- ✅ No PII (Personally Identifiable Information) storage
- ✅ Commitments are cryptographic proofs, not permissions

## IMPLEMENTATION REQUIREMENTS
- ✅ Every endpoint must connect to real UnifiedSystem methods
- ✅ Every test must use real Usenet server credentials
- ✅ Every metric must be measured, not calculated
- ✅ Every commitment must be cryptographically valid
- ✅ Every share must generate real Message-IDs
- ✅ Every error must be descriptive - no generic messages
- ✅ Every operation must be logged with real timestamps
- ✅ Every retry must respect exponential backoff

## BEFORE WRITING CODE
1. Plan the real systems you'll use
2. Identify the actual database tables
3. Specify the real NNTP operations
4. Define the actual error cases
5. Never write "will implement later"

## WHEN REVIEWING CODE
1. Search for banned patterns
2. Verify real system connections
3. Check for hardcoded test values
4. Ensure no email fields exist
5. Confirm binary access model