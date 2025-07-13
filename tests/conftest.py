"""Shared test fixtures for async testing."""

import asyncio
import tempfile
import shutil
from pathlib import Path
import pytest
from typing import Generator, List


@pytest.fixture(scope="function")
def event_loop_policy() -> Generator[asyncio.AbstractEventLoopPolicy, None, None]:
    """Create and provide a fresh event loop policy for each test function.
    
    This fixture prevents event loop conflicts and ensures proper cleanup.
    """
    original_policy = asyncio.get_event_loop_policy()
    policy = asyncio.DefaultEventLoopPolicy()
    asyncio.set_event_loop_policy(policy)
    try:
        yield policy
    finally:
        asyncio.set_event_loop_policy(original_policy)


@pytest.fixture(scope="function") 
async def clean_async_session():
    """Fixture to ensure proper cleanup of async resources."""
    # This can be used for additional async resource cleanup if needed
    yield
    # Cleanup code can go here


@pytest.fixture(scope="function")
def temp_directory():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    try:
        yield Path(temp_dir)
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def entity_stores():
    """Track EntityStore instances for proper cleanup."""
    stores: List = []
    try:
        yield stores
    finally:
        # Clean up all stores
        for store in stores:
            try:
                store.close()
            except Exception:
                pass
            try:
                asyncio.run(store.aclose())
            except Exception:
                pass