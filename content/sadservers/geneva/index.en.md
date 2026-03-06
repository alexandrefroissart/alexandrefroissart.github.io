---
title: "\"Geneva\": Renew an SSL Certificate"
date: 2026-01-25
image: "/img/banners/sadservers.png"
draft: false
reading_time: 10
categories: ["SadServers", "Linux"]
tags: ["SSL"]
---

{{< sadservers-scenario slug="geneva" >}}

The goal here is not to redo the entire Nginx configuration, but to go directly to the right place: find the certificate used, generate a new one, then check that the service presents the correct file.

## Environment

- **Service**: Nginx in HTTPS
- **Objective**: replace an expired or invalid certificate
- **Tools**: `grep`, `openssl`, `systemctl`

## Approach

### 1. Find the active SSL configuration

I start by looking where Nginx's SSL configuration references the certificate files.

```bash
grep -r "ssl" /etc/nginx/
```

This command highlights useful lines in `/etc/nginx/sites-available/default`:

```nginx
listen 443 ssl;
ssl_certificate /etc/nginx/ssl/nginx.crt;
ssl_certificate_key /etc/nginx/ssl/nginx.key;
```

The target files are therefore `/etc/nginx/ssl/nginx.crt` for the public certificate and `/etc/nginx/ssl/nginx.key` for the private key.

### 2. Regenerate a clean certificate

I then regenerate a new self-signed key/certificate pair with `openssl`.

I then replace the SSL files used by Nginx.

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout <ssl_key_path> \
  -out <ssl_certificate_path>
```

During generation, `openssl` asks for the **Distinguished Name**.

I provide values ​​consistent with the server, without publishing the exact game here.

Once the files are generated, I restart Nginx so that it supports the new certificate:

```bash
sudo systemctl restart nginx
```

### 3. Check the certificate served

I then check that Nginx presents the new certificate with `openssl s_client`.

**Date check:**
```bash
echo | openssl s_client -connect <host>:443 2>/dev/null | openssl x509 -noout -dates
```
*Expected result: `notBefore` recent, `notAfter` further back in time.*

**Topic check:**
```bash
echo | openssl s_client -connect <host>:443 2>/dev/null | openssl x509 -noout -subject
```

If the dates are correct and Nginx restarts without errors, the correction is validated.

## What I remember

- In this type of exercise, the most important thing is to quickly find the right files instead of starting from scratch.
- `openssl s_client` remains a very useful reflex to check what the service really exposes.
- A check after restart is essential: generating a certificate is not enough, you must also confirm that it is properly served.

## Skills mobilized

- OpenSSL to generate a self-signed certificate
- Reading Nginx configuration
- Verifying a certificate from the command line
- Troubleshooting of an HTTPS service
