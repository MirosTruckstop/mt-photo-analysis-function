import unittest
from unittest import mock

import main


class TestDetextText(unittest.TestCase):

    @staticmethod
    def mock_annotations(*texts: str) -> [mock.MagicMock]:
        annotations = []
        for text in texts:
            mock_annotation = mock.MagicMock()
            mock_annotation.description = text
            annotations.append(mock_annotation)
        return annotations

    def test_success(self):
        mock_annotations = mock.MagicMock()
        mock_annotations.text_annotations = self.mock_annotations('some\ntext\nö', '(e)')
        mock_vision_client = mock.MagicMock()
        mock_vision_client.text_detection.return_value = mock_annotations
        result = main.detect_text(mock_vision_client, 'http://example.org/some/image.jpeg')
        expected = ['some\ntext\nö', '(e)']
        self.assertEqual(expected, result)

    def test_empty_response(self):
        mock_annotations = mock.MagicMock()
        mock_annotations.text_annotations = []
        mock_vision_client = mock.MagicMock()
        mock_vision_client.text_detection.return_value = mock_annotations
        result = main.detect_text(mock_vision_client, 'http://example.org/some/image.jpeg')
        self.assertEqual([], result)
