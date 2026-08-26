# Security policy

## Supported versions

This portfolio project supports only the current `main` branch.

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability. Use GitHub's private
vulnerability reporting feature from the repository **Security** tab and include reproduction
steps, affected components, and potential impact.

## Deployment scope

The included Compose configuration is for local development, demonstrations, and private
Codespaces. It binds user-facing ports to localhost and generates random Codespaces credentials.
The application does not currently provide authentication or tenant isolation. Do not expose it
to an untrusted network without adding authentication, authorization, TLS termination, abuse
controls, and externally managed secrets.

Values in `.env.example` are placeholders, not production credentials. Keep `.env` untracked and
rotate any credential immediately if it is accidentally disclosed.
