#!/usr/bin/env python3
"""
Newsgroup configuration for UsenetSync
"""

# Testing configuration
TEST_NEWSGROUP = "alt.binaries.test"

# Production newsgroups (examples - configure as needed)
PRODUCTION_NEWSGROUPS = {
    "default": "alt.binaries.misc",
    "images": "alt.binaries.pictures",
    "videos": "alt.binaries.multimedia",
    "documents": "alt.binaries.misc",
    "archives": "alt.binaries.misc"
}

# Get newsgroup for testing
def get_test_newsgroup():
    """Get the newsgroup to use for testing"""
    return TEST_NEWSGROUP

# Get newsgroup for production based on content type
def get_production_newsgroup(content_type="default"):
    """Get the newsgroup to use for production posts"""
    return PRODUCTION_NEWSGROUPS.get(content_type, PRODUCTION_NEWSGROUPS["default"])

# Check if using test newsgroup
def is_test_newsgroup(newsgroup):
    """Check if the given newsgroup is for testing"""
    return newsgroup == TEST_NEWSGROUP
