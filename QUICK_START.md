# Quick Start

## 1. Install

```bash
pip install metaai-sdk[api,browser]
agent-browser install
```

## 2. Get your cookies

1. Open https://www.meta.ai/ and log in
2. Press F12 → Application → Cookies → https://www.meta.ai
3. Copy `datr` and `ecto_1_sess` values

## 3. Generate an image

```python
from metaai_api import MetaAI

ai = MetaAI(cookies={
    "datr": "YOUR_DATR",
    "ecto_1_sess": "YOUR_ECTO_1_SESS",
})

result = ai.generate_image_new("a watercolor painting of a cat")
print(result["image_urls"])

ai.close()
```

## 4. Chat

```python
reply = ai.prompt("What is the capital of France?")
print(reply["message"])
```

## 5. Run as API server

```bash
export META_AI_DATR="YOUR_DATR"
export META_AI_ECTO_1_SESS="YOUR_ECTO_1_SESS"

python -m metaai_api.api_server
```

Call from any language:
```bash
curl -X POST http://localhost:8000/generate-image \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a watercolor painting of a cat"}'
```
