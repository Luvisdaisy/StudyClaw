"""Tests for prompt_loader module."""
import pytest
from unittest.mock import patch, MagicMock

from utils.prompt_loader import load_prompt, load_system_prompts, load_rag_prompts


class TestLoadPrompt:
    """Tests for load_prompt function."""

    @patch("utils.prompt_loader.prompts_cfg", {"main_prompt_path": "prompts/main_prompts.txt"})
    @patch("utils.prompt_loader.get_abs_path")
    @patch("builtins.open", create=True)
    def test_load_prompt_main_success(self, mock_open, mock_get_abs_path):
        """Test loading main prompt successfully."""
        mock_get_abs_path.return_value = "/path/to/prompts/main_prompts.txt"
        mock_open.return_value.__enter__.return_value.read.return_value = "Main prompt content"

        result = load_prompt("main")

        assert result == "Main prompt content"
        mock_get_abs_path.assert_called_once_with("prompts/main_prompts.txt")

    @patch("utils.prompt_loader.prompts_cfg", {"rag_prompt_path": "prompts/rag_prompts.txt"})
    @patch("utils.prompt_loader.get_abs_path")
    @patch("builtins.open", create=True)
    def test_load_prompt_rag_success(self, mock_open, mock_get_abs_path):
        """Test loading RAG prompt successfully."""
        mock_get_abs_path.return_value = "/path/to/prompts/rag_prompts.txt"
        mock_open.return_value.__enter__.return_value.read.return_value = "RAG prompt content"

        result = load_prompt("rag")

        assert result == "RAG prompt content"


    @patch("utils.prompt_loader.prompts_cfg", {})
    def test_load_prompt_missing_key(self):
        """Test that KeyError is raised when prompt path is missing."""
        with pytest.raises(KeyError):
            load_prompt("main")

    @patch("utils.prompt_loader.prompts_cfg", {"main_prompt_path": "prompts/main_prompts.txt"})
    @patch("utils.prompt_loader.get_abs_path")
    @patch("builtins.open", create=True)
    def test_load_prompt_file_not_found(self, mock_open, mock_get_abs_path):
        """Test that IOError is raised when file doesn't exist."""
        mock_get_abs_path.return_value = "/path/to/nonexistent.txt"
        mock_open.side_effect = FileNotFoundError("File not found")

        with pytest.raises(FileNotFoundError):
            load_prompt("main")


class TestBackwardCompatibility:
    """Tests for backward compatibility functions."""

    @patch("utils.prompt_loader.load_prompt")
    def test_load_system_prompts(self, mock_load_prompt):
        """Test load_system_prompts calls load_prompt with 'main'."""
        mock_load_prompt.return_value = "System prompt"

        result = load_system_prompts()

        assert result == "System prompt"
        mock_load_prompt.assert_called_once_with("main")

    @patch("utils.prompt_loader.load_prompt")
    def test_load_rag_prompts(self, mock_load_prompt):
        """Test load_rag_prompts calls load_prompt with 'rag'."""
        mock_load_prompt.return_value = "RAG prompt"

        result = load_rag_prompts()

        assert result == "RAG prompt"
        mock_load_prompt.assert_called_once_with("rag")

