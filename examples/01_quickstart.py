# Install the SDK first: pip install tontaube
import tontaube
import os

API_KEY = os.getenv("TONTAUBE_API_KEY", "Insert your API key here")

with tontaube.Client(api_key=API_KEY) as client:
    voices = client.list_voices()
    for voice in voices:
        print(f"{voice.name} ({voice.voice_style or voice.type}), id: {voice.id}")

    response = client.generate_speech(
        text="I am here to help you with your project. Tell me what we are building today, and I will get right to work.",
        voice_id=voices[0].id,
        temperature=0.8,
    )

with open("speech.m4a", "wb") as f:
    f.write(response.content)

print(f"Cost: ${response.cost_usd}, Balance: ${response.balance_usd}")
print("Result saved to speech.m4a")
