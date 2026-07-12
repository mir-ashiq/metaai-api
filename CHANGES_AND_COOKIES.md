# Changes and Cookies

## Cookie Requirements

Meta AI uses cookie-based authentication. You need:

| Cookie | Required | Description |
|--------|----------|-------------|
| `datr` | ✅ Yes | Device cookie (long-lived) |
| `ecto_1_sess` | ✅ Yes | Session token (expires frequently) |
| `abra_sess` | Optional | Needed in some regions (e.g. Indonesia) |

## How to Get Cookies

1. Open https://www.meta.ai/ in Chrome/Edge
2. Log in with your Facebook account
3. Press F12 to open DevTools
4. Go to Application → Cookies → https://www.meta.ai
5. Copy the values of `datr` and `ecto_1_sess`

## Cookie Expiration

The `ecto_1_sess` cookie expires frequently (hours to days). If your requests
start failing with authentication errors, re-extract the cookies.

## Environment Variables

```bash
export META_AI_DATR="your_datr_value"
export META_AI_ECTO_1_SESS="your_ecto_1_sess_value"
export META_AI_ABRA_SESS="your_abra_sess_value"  # optional
export META_AI_ACCESS_TOKEN="your_access_token"   # for WebSocket method
```

## Access Token (for advanced WebSocket method)

The access token is needed for:
- `client.replay_frame()` — DGW frame replay
- `client.fetch_card_media()` — HTTP media fetching

To get it:
1. Open meta.ai, log in
2. DevTools → Network → WS
3. Send any message in the chat
4. Find the `wss://gateway.meta.ai/ws/clippy` connection
5. Copy the `Authorization=ecto1:...` value from the query string
