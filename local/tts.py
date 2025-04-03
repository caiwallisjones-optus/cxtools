"""Simple Azure TTS interface"""
import logging
import time
from xml.etree import ElementTree
import requests

logger = logging.getLogger("cxtools")

class Speech(object):
    """Azure TTS implementation, TTS and STT implemented"""
    subscription_key = None
    access_token = None

    def __init__(self, subscription_key ):
        self.timestr = time.strftime("%Y%m%d-%H%M")
        self.subscription_key = subscription_key

    def get_token(self):
        """This function performs the token exchange."""
        logger.info(">> get_token")
        fetch_token_url = "https://westus.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        headers = {
            "Ocp-Apim-Subscription-Key": self.subscription_key
        }
        try:
            response = requests.post(fetch_token_url, headers=headers, timeout=20000)
            self.access_token = str(response.text)
            logger.info("SubscriptionKey=%s" , self.subscription_key)
            logger.info("We got a token")
        except Exception as e:
            logger.error("<< exception at %s: \n%s", __name__, e)
            return False

        logger.info("<< get_audio")
        return True

    def get_audio(self,input_text : str ,voice_font : str) -> bytes:
        """This function calls the TTS endpoint with and existing access token."""
        logger.info(">> get_audio")
        if self.access_token is None:
            self.get_token()
        logger.info("Getting audio for font %s" , voice_font)
        base_url = "https://westus.tts.speech.microsoft.com/"
        path = "cognitiveservices/v1"
        constructed_url = base_url + path
        headers = {
            "Authorization": "Bearer " + self.access_token,
            "Content-Type": "application/ssml+xml",
            #"X-Microsoft-OutputFormat": "riff-24khz-16bit-mono-pcm",
            "X-Microsoft-OutputFormat": "riff-8khz-8bit-mono-mulaw",
            "User-Agent": "WebApp-development",
        }
        # Build the SSML request with ElementTree
        xml_body = ElementTree.Element("speak", version="1.0")
        xml_body.set("{http://www.w3.org/XML/1998/namespace}lang", "en-us")
        voice = ElementTree.SubElement(xml_body, "voice")
        voice.set("{http://www.w3.org/XML/1998/namespace}lang", "en-US")
        voice.set("name", "en-AU-NatashaNeural")
        voice.text = input_text
        # The body must be encoded as UTF-8 to handle non-ascii characters.
        body = ElementTree.tostring(xml_body, encoding="utf-8")

        #Send the request
        response = requests.post(constructed_url, headers=headers, data=body, timeout=20000)

        logger.info("Response reason %s" , response.reason)

        # Write the response as a wav file for playback. The file is located
        # in the same directory where this sample is run.
        logger.info("<< get_audio")
        return response.content

    def get_text(self,filename :str ) -> str:
        #logger.info("Getting Text")
        #https://{SERVICE_REGION}.api.cognitive.microsoft.com/speechtotext/v3.1
        #base_url = "https://westus.api.cognitive.microsoft.com/"
        #path = "speechtotext/v3.1"
        #constructed_url = base_url + path
        constructed_url = "https://westus.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language=en-AU&format=detailed"

        headers = {
            "Ocp-Apim-Subscription-Key" : self.subscription_key,
            "Content-Type": "audio/wav",
            "User-Agent": "WebApp-development",
        }

        with open(filename, "rb") as wav_file:
            wav_data = wav_file.read()
            response = requests.post(constructed_url, headers=headers, data=wav_data , timeout= 20000)

        #logger.info("Response reason %s" , response.reason)
        #logger.info("Response content %s" , response.content)

        # Write the response as a wav file for playback. The file is located
        # in the same directory where this sample is run.
        return response.json().get("NBest")
