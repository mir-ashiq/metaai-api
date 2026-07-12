"""Chat example — text conversation with Meta AI."""
from metaai_api import MetaAI

ai = MetaAI(cookies={
    "datr": "YOUR_DATR",
    "ecto_1_sess": "YOUR_ECTO_1_SESS",
})

reply = ai.prompt("What is the capital of France?")
print(reply["message"])

ai.close()
