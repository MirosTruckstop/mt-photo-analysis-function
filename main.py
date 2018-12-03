import base64
from google.cloud import vision

vision_client = vision.ImageAnnotatorClient()


def detect_text(image_uri):
    print('Looking for text in image {}'.format(image_uri))
    text_detection_response = vision_client.text_detection({
        'source': {'image_uri': image_uri}
    })
    annotations = text_detection_response.text_annotations
    if len(annotations) > 0:
        text = annotations[0].description
    else:
        text = ''
    print('Extracted text {} from image ({} chars).'.format(text, len(text)))


def photo_analysis(data, _context):
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         data (dict): The dictionary with data specific to this type of event.
         _context (google.cloud.functions.Context): The Cloud Functions event metadata.
    """
    if 'data' not in data:
        return
    name = base64.b64decode(data['data']).decode('utf-8')
    detect_text(name)
