from gtts import gTTS

def generate_audio(text, outputFilename):
    tts = gTTS(text=text, lang="en")
    tts.save(outputFilename)
