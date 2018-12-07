import base64
import datetime
import hashlib
import logging

from google.cloud import vision
from google.cloud import firestore


def detect_text(vision_client: vision.ImageAnnotatorClient, image_uri: str) -> [str]:
    logging.info('Looking for text in image \'{}\''.format(image_uri))
    text_detection_response = vision_client.text_detection({
        'source': {'image_uri': image_uri}
    })
    annotations = text_detection_response.text_annotations
    texts = []
    for annotation in annotations:
        texts.append(annotation.description)
    logging.info('Extracted texts \'{}\' from image.'.format(texts))
    return texts


def normalize_text(texts: [str]) -> [str]:
    res = []
    for text in texts:
        if len(text) <= 1:
            continue
        res.append(text.lower())
    return res


def photo_id(image_uri: str) -> str:
    return hashlib.md5(image_uri.encode('utf-8')).hexdigest()


def store(client: firestore.Client, document: str, data: dict, collection: str='photos'):
    logging.info('Store data in \'{}\''.format(collection))
    doc_ref = client.collection(collection).document(document)
    doc_ref.set(data)


def do_photo_anaysis(data: dict, vision_client: vision.ImageAnnotatorClient, firestore_client: firestore.Client,
                     now: datetime.datetime=None):
    data = data.get('data')
    if not data:
        return

    image_uri = base64.b64decode(data).decode('utf-8')
    texts = detect_text(vision_client, image_uri)
    if texts:
        raw_texts = texts[0]  # The vision API returns the whole raw string at index zero
        texts = normalize_text(texts[1:])
        data = ({
            'uri': image_uri,
            'texts': texts,
            'raw_texts': raw_texts,
            'updated': datetime.datetime.now() if not now else now
        })
        store(firestore_client, photo_id(image_uri), data)


def photo_analysis(data, _context):
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         data (dict): The dictionary with data specific to this type of event.
         _context (google.cloud.functions.Context): The Cloud Functions event metadata.
    """
    do_photo_anaysis(
        data,
        vision_client=vision.ImageAnnotatorClient(),
        firestore_client=firestore.Client()
    )
