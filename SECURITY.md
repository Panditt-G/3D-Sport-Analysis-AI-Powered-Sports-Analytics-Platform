# Security Policy

## Supported Versions

The following versions of the **Sports AI Analytics Platform** currently receive security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Reporting a Vulnerability

If you discover a security vulnerability within this repository, please report it responsibly:

1. **Do Not Open a Public Issue**: To protect users, please do not disclose security vulnerabilities publicly in GitHub Issues or Discussions.
2. **How to Report**: Please reach out directly to the repository maintainer via email or private security disclosure.
3. **Information to Include**:
   - Clear description of the vulnerability and its potential impact.
   - Steps or proof-of-concept to reproduce the issue.
   - Relevant log outputs or screenshots.

---

## Security Best Practices

- **CORS Configuration**: Restrict allowed origins in `backend/server.py` before deploying to a production environment.
- **Secrets Management**: Keep credentials, tokens, and private keys inside `.env` files and never commit them to git.
- **Input Validation**: Keep strict file type (`.mp4`, `.mov`, `.avi`) and file size limits enforced on video upload endpoints.
