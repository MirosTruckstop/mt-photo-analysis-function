import base64
import datetime
import unittest
from unittest import mock
from urllib import parse
import requests
import httmock

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
        mock_annotations.text_annotations = self.mock_annotations('Some Text\nAnother ö (e)\n', 'Some', 'Text',
                                                                  'Another', 'ö', '(e)')
        mock_vision_client = mock.MagicMock()
        mock_vision_client.text_detection.return_value = mock_annotations
        result = main.detect_text(mock_vision_client, 'http://example.org/some/image.jpeg')
        expected = ['Some Text\nAnother ö (e)\n', 'Some', 'Text', 'Another', 'ö', '(e)']
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


class TestDecodeMsg(unittest.TestCase):

    @staticmethod
    def create_msg_data(data: str):
        return base64.b64encode(data.encode('utf-8'))

    def test_no_attributes(self):
        msg = {}
        self.assertRaises(main.InvalidMassageError, main.decode_msg, msg)

    def test_no_image_id(self):
        msg = {'attributes': {}}
        self.assertRaises(main.InvalidMassageError, main.decode_msg, msg)

    def test_no_data(self):
        msg = {'attributes': {'id': '1234'}}
        self.assertRaises(main.InvalidMassageError, main.decode_msg, msg)

    def test_no_json(self):
        data = TestDecodeMsg.create_msg_data('no json')
        msg = {
            'attributes': {'id': '1234'},
            'data': data
        }
        self.assertRaises(main.InvalidMassageError, main.decode_msg, msg)

    def test_no_jwt(self):
        data = TestDecodeMsg.create_msg_data('{"image_uri":"https://example.org/some/path/to/a/image.jpeg"}')
        msg = {
            'attributes': {'id': '1234'},
            'data': data
        }
        self.assertRaises(main.InvalidMassageError, main.decode_msg, msg)

    def test_no_image_uri(self):
        data = TestDecodeMsg.create_msg_data('{"jwt":"asd561"}')
        msg = {
            'attributes': {'id': '1234'},
            'data': data
        }
        self.assertRaises(main.InvalidMassageError, main.decode_msg, msg)

    def test_success(self):
        data = TestDecodeMsg.create_msg_data(
            '{"image_uri":"https://example.org/some/path/to/a/image.jpeg","jwt":"asd561"}')
        msg = {
            'attributes': {'id': '1234'},
            'data': data
        }
        expected = {
            'image_id': '1234',
            'image_uri': 'https://example.org/some/path/to/a/image.jpeg',
            'jwt': 'asd561',
        }
        actual = main.decode_msg(msg)
        self.assertEqual(expected, actual)


class TestFunction(unittest.TestCase):

    @staticmethod
    def create_msg_data(data: str):
        return base64.b64encode(data.encode('utf-8'))

    # pylint: disable=no-self-use
    def test_all(self):
        # Mock vision client
        mock_annotations = mock.MagicMock()
        mock_annotations.text_annotations = TestDetextText.mock_annotations(
            'some Text\nMessage ö (e)\n', 'some', 'Text', 'Message', 'ö', '(e)'
        )
        mock_vision_client = mock.MagicMock()
        mock_vision_client.text_detection.return_value = mock_annotations

        data = TestFunction.create_msg_data(
            '{"image_uri":"https://example.org/some/path/to/a/image.jpeg","jwt":"asd561"}')
        msg = {
            'data': data,
            'attributes': {
                'id': '3001'
            }
        }

        @httmock.urlmatch(netloc=r'(.*\.)?example\.org$')
        def wp_mock(url: str, request: requests.PreparedRequest):
            assert url == parse.SplitResult(scheme='https', netloc='example.org',
                                            path='/wp-json/mt-wp-photo-analysis/v1/text/3001', query='', fragment='')
            assert request.method == 'PUT'
            assert request.headers['Authorization'] == 'Bearer asd561'
            assert request.headers['Content-Type'] == 'application/json'
            assert request.body == b'{"textAnnotations": "some Text Message (e)"}'
            return {
                'status_code': 200,
                'content': 'OK'
            }

        with mock.patch.dict('os.environ', {'WP_HOST': 'https://example.org'}):
            with httmock.HTTMock(wp_mock):
                main.do_photo_anaysis(
                    msg,
                    vision_client=mock_vision_client,
                    now=datetime.datetime(2018, 12, 7, 23, 41, 11)
                )
