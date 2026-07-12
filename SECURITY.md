# Security

## Cookie Handling

This project uses your Meta AI browser cookies for authentication. These cookies
give full access to your Meta AI account. Treat them like passwords.

### Best Practices
- Never commit cookies to git
- Never share cookies in issues or discussions
- Use environment variables to pass cookies
- Rotate cookies if you suspect they've been compromised
- The `.gitignore` file excludes common cookie file patterns

## API Key

When deploying the API server, always set `META_AI_API_KEY` to prevent
unauthorized access to your deployment.

## Responsible Use

- Do not use this tool to violate Meta's Terms of Service
- Do not use this tool for spam or abuse
- Respect rate limits
- This is an unofficial tool — use at your own risk
