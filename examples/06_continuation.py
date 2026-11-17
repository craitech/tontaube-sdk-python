import io
import wave
import tontaube
import os

API_KEY = os.getenv("TONTAUBE_API_KEY", "Insert your API key here")
FIRST = "The lighthouse keeper climbed the stairs one last time."
SECOND = "At the top, he lit the lamp and watched the ships come home."

with tontaube.Client(api_key=API_KEY) as client:
    voice = client.list_voices(type="library")[0]

    first = client.generate_speech(text=FIRST, voice_id=voice.id, return_context=True)
    second = client.generate_speech(
        text=SECOND,
        voice_id=voice.id,
        prefix=tontaube.Prefix(text=FIRST, context=[first.context_slice()]),
        return_context=True,
    )

frames = b""
for part in (first, second):
    with wave.open(io.BytesIO(part.content)) as audio:
        params = audio.getparams()
        frames += audio.readframes(audio.getnframes())

with wave.open("story.wav", "wb") as out:
    out.setparams(params)
    out.writeframes(frames)

print("Result saved to story.wav")
