import base64
import datetime
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
        mock_annotations.text_annotations = self.mock_annotations('some\ntext\nö (e)', 'some\ntext\nö', '(e)')
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


class TestNormalizeText(unittest.TestCase):

    def test_too_short(self):
        result = main.normalize_text(['', 'a'])
        self.assertEqual([], result)

    def test_to_lower(self):
        result = main.normalize_text(['HellO', 'WorLd'])
        self.assertEqual(['hello', 'world'], result)


class TestPhotoId(unittest.TestCase):

    def test_url(self):
        result = main.photo_id('https://example.org/some/path/to/a/image.jpeg')
        self.assertEqual('96699843dec8204f4eb0289a30a1f202', result)


class TestStore(unittest.TestCase):

    def test_storage(self):
        mock_document = mock.MagicMock()
        mock_document.set = mock.MagicMock()
        mock_collection = mock.MagicMock()
        mock_collection.document.return_value = mock_document
        mock_firestore_client = mock.MagicMock()
        mock_firestore_client.collection.return_value = mock_collection

        main.store(mock_firestore_client, 'document', {'some key': 'some value'})
        # Check the correct collection was chosen
        mock_firestore_client.collection.assert_called_once_with('photos')
        # Check the correct document was chosen
        mock_collection.document.assert_called_once_with('document')
        # Check set method is called with the correct data
        mock_document.set.assert_called_once_with({'some key': 'some value'})


class TestFunction(unittest.TestCase):

    def test_all(self):
        # Mock vision client
        mock_annotations = mock.MagicMock()
        mock_annotations.text_annotations = TestDetextText.mock_annotations(
            'some Text Message ö (e)', 'some', 'Text', 'Message', 'ö', '(e)'
        )
        mock_vision_client = mock.MagicMock()
        mock_vision_client.text_detection.return_value = mock_annotations

        # Mock firestore client
        mock_document = mock.MagicMock()
        mock_document.set = mock.MagicMock()
        mock_collection = mock.MagicMock()
        mock_collection.document.return_value = mock_document
        mock_firestore_client = mock.MagicMock()
        mock_firestore_client.collection.return_value = mock_collection

        data = {
            'data': base64.b64encode('https://example.org/some/path/to/a/image.jpeg'.encode('utf-8'))
        }

        main.do_photo_anaysis(
            data,
            vision_client=mock_vision_client,
            firestore_client=mock_firestore_client,
            now=datetime.datetime(2018, 12, 7, 23, 41, 11)
        )
        mock_document.set.assert_called_once_with({
            'uri': 'https://example.org/some/path/to/a/image.jpeg',
            'texts': ['some', 'text', 'message', '(e)'],
            'updated': datetime.datetime(2018, 12, 7, 23, 41, 11)
        })
