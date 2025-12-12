from gtts import gTTS

def generate_audio(text, outputFilename):
    tts = gTTS(text=text, lang="vi")
    tts.save(outputFilename)