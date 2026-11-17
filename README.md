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
    speakers = client.list_speakers()
    response = client.generate_speech(
        text="Tell me what we are building today, and I will get right to work.",
        speaker_id=speakers[0].id,
    )

with open("speech.wav", "wb") as f:
    f.write(response.content)
```

Async client is also available via `tontaube.AsyncClient`. See the [examples/](examples/) folder for more usage patterns.

For full API reference see [tontaube.ai/api-reference](https://tontaube.ai/api-reference).
