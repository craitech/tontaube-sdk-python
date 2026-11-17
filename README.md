# tontaube

Python SDK for the [Tontaube](https://tontaube.ai) text-to-speech API.

## Installation

```bash
pip install tontaube
```

## Usage

```python
import tontaube

with tontaube.Client(api_key="your-api-key") as client:
    voices = client.list_voices()
    response = client.generate_speech(
        text="Tell me what we are building today, and I will get right to work.",
        voice_id=voices[0].id,
    )

with open("speech.m4a", "wb") as f:
    f.write(response.content)
```

Audio is returned as Opus in an MP4 container. Async client is also available via `tontaube.AsyncClient`.

## Your own voices

```python
voice = client.create_voice(name="My voice", audio="reference.wav", language="en")
response = client.generate_speech(text="Hello in my own voice.", voice_id=voice.id)
```

`list_voices()` returns your voices and the Tontaube library voices, `get_voice()` and `delete_voice()` manage them.
For a one-off voice without storing it, pass the recording directly: `generate_speech(text, voice_audio="reference.wav")`.

## Streaming

```python
with open("speech.mp3", "wb") as f:
    for chunk in client.stream_speech(text="Hello while it is still being generated.", voice_id=voice.id):
        f.write(chunk)
```

## More options

- `style` (`audiobook`, `conversational`, `agentic`) and `controls=tontaube.Controls(rate=1, pause=3)` shape the delivery.
- `seed` makes a generation repeatable.
- `style`, `controls`, `seed` and `prefix` work for streaming too.
- `include_timestamps=True` returns when each word is spoken (English).
- `return_context=True` and `prefix` continue earlier speech seamlessly.

Errors from the API raise `tontaube.APIError` with `status_code`, `code` and `message`.

See the [examples/](examples/) folder for more usage patterns.

For full API reference see [tontaube.ai/api-reference](https://tontaube.ai/api-reference).
