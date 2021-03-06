import json
import os

import base64
import datetime
import logging
import requests

from google.cloud import vision

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class InvalidMassageError(Exception):
    pass


def detect_text(vision_client: vision.ImageAnnotatorClient, image_uri: str) -> [str]:
    logging.info('Looking for text in image \'%s\'', image_uri)
    text_detection_response = vision_client.text_detection({
        'source': {'image_uri': image_uri}
    })
    annotations = text_detection_response.text_annotations
    texts = []
    for annotation in annotations:
        texts.append(annotation.description)
    logging.info('Extracted texts \'%s\' from image.', texts)
    return texts


def normalize_text(texts: [str]) -> [str]:
    res = []
    for text in texts:
        if len(text) <= 1:
            continue
        res.append(text)
    return res


def wordpress_put_texts(data: dict, jwt: str):
    # pylint: disable=fixme
    # TODO: Parse dict instead of accessing envs.
    resp = requests.put(
        '{host}/wp-json/mt-wp-photo-analysis/v1/text/{id}'.format(host=format(os.environ['WP_HOST']), id=data['id']),
        headers={
            'Authorization': 'Bearer {}'.format(jwt),
            'Content-Type': 'application/json',
        },
        json={'textAnnotations': ' '.join(data['texts'])})
    if resp.status_code != 200:
        logging.warning('%s response from ¸\'%s\': %s', resp.status_code, resp.url, resp.text)


def decode_msg(msg: dict):
    attributes = msg.get('attributes')
    if not attributes:
        raise InvalidMassageError('message has no attributes')
    image_id = attributes.get('id')
    if not image_id:
        raise InvalidMassageError('message has not attribute \'id\'')

    data = msg.get('data')
    if not data:
        raise InvalidMassageError('message has no data')
    data_encoded = base64.b64decode(data).decode('utf-8')
    try:
        data_json = json.loads(data_encoded)
    except json.decoder.JSONDecodeError as err:
        raise InvalidMassageError('message data is no valid json: \'%s\'' % err)
    if 'image_uri' not in data_json:
        raise InvalidMassageError('message data does not contain \'image_uri\'')
    if 'jwt' not in data_json:
        raise InvalidMassageError('message data does not contain \'jwt\'')
    return {
        'image_id': image_id,
        'image_uri': data_json['image_uri'],
        'jwt': data_json['jwt']
    }


def do_photo_anaysis(msg: dict, vision_client: vision.ImageAnnotatorClient, now: datetime.datetime = None):
    msg_data = decode_msg(msg)
    texts = detect_text(vision_client, msg_data['image_uri'])
    if texts:
        raw_texts = texts[0]  # The vision API returns the whole raw string at index zero
        texts = normalize_text(texts[1:])
        data = ({
            'id': msg_data['image_id'],
            'uri': msg_data['image_uri'],
            'texts': texts,
            'raw_texts': raw_texts,
            'updated': datetime.datetime.now() if not now else now
        })
        wordpress_put_texts(data, msg_data['jwt'])


def photo_analysis(data, _context):
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         data (dict): The dictionary with data specific to this type of event.
         _context (google.cloud.functions.Context): The Cloud Functions event metadata.
    """
    do_photo_anaysis(
        data,
        vision_client=vision.ImageAnnotatorClient()
    )
