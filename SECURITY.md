# Security Policy - Meta AI Python SDK

## 🔒 Reporting Security Vulnerabilities

We take the security of Meta AI Python SDK seriously. If you discover a security vulnerability, please follow these steps:

### ⚠️ Do NOT:

- Open a public GitHub issue
- Disclose the vulnerability publicly
- Test the vulnerability on production systems

### ✅ Do:

1. **Email us privately** at: `security@meta-ai-sdk.dev`
2. **Include detailed information:**
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)
   - Your contact information

### What to Expect:

- **Initial Response**: Within 48 hours
- **Assessment**: Within 5 business days
- **Fix Timeline**: Depends on severity (see below)
- **Credit**: We'll credit you in the security advisory (if desired)

## 🛡️ Severity Levels

### Critical (Fix within 24-48 hours)

- Remote code execution
- Authentication bypass
- Data exposure of sensitive information
- Privilege escalation

### High (Fix within 1 week)

- SQL injection
- Cross-site scripting (XSS)
- Insecure deserialization
- Significant information disclosure

### Medium (Fix within 2 weeks)

- Cross-site request forgery (CSRF)
- Denial of service
- Weak cryptography
- Path traversal

### Low (Fix in next release)

- Information leaks with minimal impact
- Minor configuration issues
- Best practice violations

## 🔐 Security Best Practices for Users

### Cookie Management

```python
# ✅ Good: Use environment variables
import os
cookies = {
    "datr": os.getenv("META_AI_DATR"),
    "abra_sess": os.getenv("META_AI_ABRA_SESS")
}

# ❌ Bad: Hardcoded credentials
cookies = {
    "datr": "abc123...",  # Don't do this!
    "abra_sess": "xyz789..."
}
```

### Secure Storage

```python
# ✅ Good: Load from secure file
import json
with open("secrets.json") as f:
    cookies = json.load(f)

# Make sure secrets.json is in .gitignore!
```

### Environment Variables

```bash
# Set environment variables
export META_AI_DATR="your_datr_value"
export META_AI_ABRA_SESS="your_abra_sess_value"
```

### Proxy Usage

```python
# Use proxy for additional security/privacy
proxy = {
    'http': 'http://proxy:port',
    'https': 'https://proxy:port'
}
ai = MetaAI(cookies=cookies, proxy=proxy)
```

## 🔍 Known Security Considerations

### 1. Cookie Expiration

- **Issue**: Browser cookies expire after 24-48 hours
- **Impact**: Requires manual refresh
- **Mitigation**: Implement regular cookie refresh in your application

### 2. Token Storage

- **Issue**: Tokens stored in memory during execution
- **Impact**: Potential memory dump exposure
- **Mitigation**: Use secure execution environments

### 3. Network Traffic

- **Issue**: HTTPS only, but traffic visible to Meta
- **Impact**: Meta can see all requests
- **Mitigation**: Use proxies if privacy is critical

### 4. Rate Limiting

- **Issue**: No built-in rate limiting
- **Impact**: Potential account suspension
- **Mitigation**: Implement your own rate limiting

## 📋 Security Checklist

Before deploying applications using this SDK:

- [ ] Store credentials securely (environment variables/secrets manager)
- [ ] Never commit credentials to version control
- [ ] Use HTTPS for all communications
- [ ] Implement rate limiting
- [ ] Log security-relevant events
- [ ] Keep the SDK updated to latest version
- [ ] Review Meta's Terms of Service
- [ ] Implement proper error handling (don't expose internals)
- [ ] Use virtual environments
- [ ] Regularly rotate cookies/credentials

## 🔄 Update Policy

### Security Updates

- **Critical**: Immediate patch release
- **High**: Within 1 week
- **Medium/Low**: Next scheduled release

### Notification Channels

- GitHub Security Advisories
- Release notes (CHANGELOG.md)
- PyPI release descriptions

### Supported Versions

| Version | Supported |
| ------- | --------- |
| 2.0.x   | ✅ Yes    |
| < 2.0   | ❌ No     |

## 🚨 Past Security Issues

Currently none reported.

## 📞 Contact

- **Security Issues**: security@meta-ai-sdk.dev
- **General Issues**: GitHub Issues
- **General Questions**: GitHub Discussions

## ⚖️ Responsible Disclosure

We follow responsible disclosure practices:

1. **Report received** → Acknowledge within 48h
2. **Issue confirmed** → Assess severity
3. **Fix developed** → Test thoroughly
4. **Release prepared** → Version bump
5. **Public disclosure** → After fix is released
6. **Credit given** → In security advisory

## 🏆 Hall of Fame

Security researchers who responsibly disclose vulnerabilities will be listed here (with permission).

Currently empty - be the first!

---

**Thank you for helping keep Meta AI Python SDK secure!** 🔒
