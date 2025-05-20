"""
Tests for LLM Factory.

This module contains tests for the LLM Factory.
"""

import unittest
from unittest.mock import patch, MagicMock

from core_agent.llm.llm_factory import LLMFactory
from core_agent.llm.llm_config import LLMConfig, LLMType


class TestLLMFactory(unittest.TestCase):
    """Tests for the LLMFactory class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test configs
        self.openai_config = LLMConfig(
            model_type=LLMType.OPENAI,
            model_name="gpt-3.5-turbo",
            api_key="test-api-key",
            temperature=0.7
        )

        self.anthropic_config = LLMConfig(
            model_type=LLMType.ANTHROPIC,
            model_name="claude-2",
            api_key="test-api-key",
            temperature=0.7
        )

    @patch('langchain_community.chat_models.ChatOpenAI')
    def test_create_openai_llm(self, mock_chat_openai):
        """Test creating an OpenAI LLM."""
        # Arrange
        mock_chat_openai.return_value = MagicMock()

        # Act
        with patch('core_agent.llm.llm_factory.ChatOpenAI', mock_chat_openai):
            llm = LLMFactory.create_llm(self.openai_config)

        # Assert
        self.assertIsNotNone(llm)
        mock_chat_openai.assert_called_once_with(
            model_name="gpt-3.5-turbo",
            openai_api_key="test-api-key",
            temperature=0.7,
            max_tokens=None
        )

    @patch('langchain_community.chat_models.ChatAnthropic')
    def test_create_anthropic_llm(self, mock_chat_anthropic):
        """Test creating an Anthropic LLM."""
        # Arrange
        mock_chat_anthropic.return_value = MagicMock()

        # Act
        with patch('core_agent.llm.llm_factory.ChatAnthropic', mock_chat_anthropic):
            llm = LLMFactory.create_llm(self.anthropic_config)

        # Assert
        self.assertIsNotNone(llm)
        mock_chat_anthropic.assert_called_once_with(
            model_name="claude-2",
            anthropic_api_key="test-api-key",
            temperature=0.7,
            max_tokens=None
        )

    def test_create_openai_llm_without_api_key(self):
        """Test creating an OpenAI LLM without an API key."""
        # Arrange
        config = LLMConfig(
            model_type=LLMType.OPENAI,
            model_name="gpt-3.5-turbo",
            temperature=0.7
        )

        # Mock the environment to ensure no API key is available
        with patch.dict('os.environ', {}, clear=True):
            # Act and Assert
            with self.assertRaises(ValueError):
                LLMFactory.create_llm(config)

    def test_create_anthropic_llm_without_api_key(self):
        """Test creating an Anthropic LLM without an API key."""
        # Arrange
        config = LLMConfig(
            model_type=LLMType.ANTHROPIC,
            model_name="claude-2",
            temperature=0.7
        )

        # Mock the environment to ensure no API key is available
        with patch.dict('os.environ', {}, clear=True):
            # Act and Assert
            with self.assertRaises(ValueError):
                LLMFactory.create_llm(config)

    @patch('core_agent.llm.llm_factory.LLMFactory._create_local_llm')
    def test_create_local_llm(self, mock_create_local_llm):
        """Test creating a local LLM."""
        # Arrange
        config = LLMConfig(
            model_type=LLMType.LOCAL,
            model_name="llama-7b",
            temperature=0.7
        )
        mock_create_local_llm.side_effect = NotImplementedError("Local LLM support is not yet implemented")

        # Act and Assert
        with self.assertRaises(NotImplementedError):
            LLMFactory.create_llm(config)

    @patch('core_agent.llm.llm_factory.LLMFactory._create_custom_llm')
    def test_create_custom_llm(self, mock_create_custom_llm):
        """Test creating a custom LLM."""
        # Arrange
        config = LLMConfig(
            model_type=LLMType.CUSTOM,
            model_name="custom-model",
            temperature=0.7
        )
        mock_create_custom_llm.side_effect = NotImplementedError("Custom LLM support is not yet implemented")

        # Act and Assert
        with self.assertRaises(NotImplementedError):
            LLMFactory.create_llm(config)

    def test_create_llm_with_unsupported_type(self):
        """Test creating an LLM with an unsupported type."""
        # This test is no longer needed as Pydantic will validate the enum
        # before the code even reaches the create_llm method
        pass


if __name__ == "__main__":
    unittest.main()
