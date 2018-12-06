import base64
import logging
from google.cloud import vision


def detect_text(vision_client: vision.ImageAnnotatorClient, image_uri: str) -> [str]:
    logging.info('Looking for text in image {}'.format(image_uri))
    text_detection_response = vision_client.text_detection({
        'source': {'image_uri': image_uri}
    })
    annotations = text_detection_response.text_annotations
    texts = []
    for annotation in annotations:
        texts.append(annotation.description)
    logging.info('Extracted texts \'{}\' from image.'.format(texts))
    return texts


def photo_analysis(data, _context):
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         data (dict): The dictionary with data specific to this type of event.
         _context (google.cloud.functions.Context): The Cloud Functions event metadata.
    """
    if 'data' not in data:
        return
    name = base64.b64decode(data['data']).decode('utf-8')
    detect_text(vision.ImageAnnotatorClient(), name)
