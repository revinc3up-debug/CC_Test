"""Tests for LLM adapter layer."""

import os
import pytest
from pathlib import Path

from framework.adapter import (
    LLMResponse,
    FileAdapter,
    create_adapter,
)


class TestLLMResponse:
    def test_basic_creation(self):
        r = LLMResponse(content="Hello", model="test-model")
        assert r.content == "Hello"
        assert r.role == "assistant"


class TestFileAdapter:
    def test_saves_prompt_to_file(self, tmp_path):
        adapter = FileAdapter(output_dir=str(tmp_path))
        response = adapter.send("What is 2+2?", system_prompt="You are helpful.")
        assert "saved to" in response.content

        files = list(tmp_path.glob("*.md"))
        assert len(files) == 1

        content = files[0].read_text()
        assert "What is 2+2?" in content
        assert "You are helpful." in content

    def test_increments_counter(self, tmp_path):
        adapter = FileAdapter(output_dir=str(tmp_path))
        adapter.send("Prompt 1")
        adapter.send("Prompt 2")
        adapter.send("Prompt 3")

        files = sorted(tmp_path.glob("*.md"))
        assert len(files) == 3
        assert "001" in files[0].name
        assert "003" in files[2].name

    def test_name(self, tmp_path):
        adapter = FileAdapter(output_dir=str(tmp_path))
        assert adapter.name().startswith("file:")


class TestCreateAdapter:
    def test_file_adapter(self, tmp_path):
        adapter = create_adapter("file", output_dir=str(tmp_path))
        assert isinstance(adapter, FileAdapter)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            create_adapter("nonexistent_provider")

    def test_anthropic_adapter_creation(self):
        # Just test creation, not actual API call
        adapter = create_adapter("anthropic", model="claude-sonnet-4-20250514")
        assert adapter.name() == "anthropic:claude-sonnet-4-20250514"

    def test_openai_adapter_creation(self):
        adapter = create_adapter("openai", model="gpt-4o")
        assert adapter.name() == "openai:gpt-4o"
