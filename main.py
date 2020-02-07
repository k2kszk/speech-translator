#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask
from flask import request
from flask import render_template
from flask import send_file
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
import os
import io
import argparse
from google.cloud import translate_v2 as translate
import six
from google.cloud import texttospeech
import html


app = Flask(__name__)

@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == "POST":
        f = open('/tmp/file.wav', 'wb')
        f.write(request.files['audio_data'].read())
        f.close()

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="credentials.json"
        client = speech.SpeechClient()
        with io.open('/tmp/file.wav', 'rb') as audio_file:
            content = audio_file.read()

        audio = types.RecognitionAudio(content=content)
        config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code='ja-JP',
            enable_automatic_punctuation=True)
        response = client.recognize(config, audio)
        
        resultsentence = list()
        for result in response.results:
            # The first alternative is the most likely one for this portion.
            sentence = '{}'.format(result.alternatives[0].transcript)
            resultsentence.append(sentence)
        
        print(resultsentence)
        resultsentence = " ".join(resultsentence)
        return render_template("translate.html", resultsentence=resultsentence)
    else:
        return render_template("index.html")

@app.route("/translate", methods=['POST', 'GET'])
def result():
    if request.method == "POST":
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="credentials.json"
        translate_client = translate.Client()
        data = request.form['text']
        model = 'nmt'
        target = 'en'
        result = translate_client.translate(data, target_language=target, model=model)

        translationresult = '{}'.format(result['translatedText'])
        print(translationresult)
        translationresult = html.unescape(translationresult)

        return render_template("synthesize.html", translationresult=translationresult)
    else:
        return render_template("translate.html")


@app.route("/synthesize", methods=['POST', 'GET'])
def synthesize():
    if request.method == "POST":
        ssml = '<speak><prosody rate="slow">' + request.form['text'] + '</prosody></speak>'
        accent = request.form['accent']
        voiceid = next(voice for voice in request.form.getlist('voiceId[]') if accent in voice)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="credentials.json"
 
        client = texttospeech.TextToSpeechClient()
        input_text = texttospeech.types.SynthesisInput(ssml=ssml)
        voice = texttospeech.types.VoiceSelectionParams(
            language_code=accent,
            name=voiceid)

        audio_config = texttospeech.types.AudioConfig(
            audio_encoding=texttospeech.enums.AudioEncoding.MP3)

        response = client.synthesize_speech(input_text, voice, audio_config)

        # The response's audio_content is binary.
        with open('/tmp/output.mp3', 'wb') as out:
            out.write(response.audio_content)

        return send_file("/tmp/output.mp3",as_attachment=True)
    else:
        return render_template("synthesize.html")
if __name__ == "__main__":
    app.run()