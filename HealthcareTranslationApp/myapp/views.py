from django.shortcuts import render
from django.http import JsonResponse
from google.cloud import speech, texttospeech, translate_v2 as translate
from django.middleware.csrf import get_token
import os
import tempfile

speech_client = speech.SpeechClient()
translate_client = translate.Client()
text_to_speech_client = texttospeech.TextToSpeechClient()


languages = translate_client.get_languages()


def speech_to_text(audio_data):
    audio = speech.RecognitionAudio(content=audio_data)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code="en-US",
    )
    response = speech_client.recognize(config=config, audio=audio)
    return response.results[0].alternatives[0].transcript


def translate_text(text, target_language):
    result = translate_client.translate(text, target_language=target_language)
    return result['translatedText']


def text_to_speech_convert(text, language_code="en-US"):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = text_to_speech_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    return response.audio_content


def translate_and_audio(request):
    if request.method == 'POST':
        original_text = request.POST.get('original_text')
        target_language = request.POST.get('target_language', 'es')

        translated_text = translate_text(original_text, target_language)

        audio_content = text_to_speech_convert(translated_text, language_code="es-US")

        return JsonResponse({'translated_text': translated_text, 'audio': audio_content.hex()})
    else:
        csrf_token = get_token(request)
        response=render(request, 'myapp/index.html', {'languages': languages})

        response.set_cookie('csrftoken', csrf_token)
        return response

def upload_audio(request):
    if request.method == 'POST' and request.FILES.get('audio'):
        audio_file = request.FILES['audio']
        input_language = request.POST.get('input_language', 'en-US')

        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_audio:
            for chunk in audio_file.chunks():
                temp_audio.write(chunk)
            temp_filename = temp_audio.name

        try:
            client = speech.SpeechClient()

            with open(temp_filename, 'rb') as f:
                audio_content = f.read()

            audio = speech.RecognitionAudio(content=audio_content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=48000,
                language_code=input_language,
                enable_automatic_punctuation=True,
            )

            response = client.recognize(config=config, audio=audio)

            transcript = ''
            for result in response.results:
                transcript += result.alternatives[0].transcript

            return JsonResponse({'transcribed_text': transcript})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        finally:
            os.remove(temp_filename)

    return JsonResponse({'error': 'No audio file found'}, status=400)
        
