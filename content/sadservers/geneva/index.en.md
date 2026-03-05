---
title: "\"Geneva\": Renew an SSL Certificate"
date: 2026-01-25
image: "/img/banners/sadservers.png"
draft: false
reading_time: 10
categories: ["SadServers", "Linux"]
tags: ["ssl"]
---

{{< sadservers-scenario slug="geneva" >}}

---

## Context

There is an Nginx web server running on this machine, configured to serve a simple site over HTTPS. However, the current certificate has expired or is invalid. The goal is to renew the SSL certificate.

---

## Analysis

I start by looking up where the Nginx SSL configuration is to identify the certificate files used.

```bash
grep -r "ssl" /etc/nginx/
```

This command reveals the interesting lines in `/etc/nginx/sites-available/default`:

```nginx
listen 443 ssl;
ssl_certificate /etc/nginx/ssl/nginx.crt;
ssl_certificate_key /etc/nginx/ssl/nginx.key;
```

The target files are therefore `/etc/nginx/ssl/nginx.crt` (the public certificate) and `/etc/nginx/ssl/nginx.key` (the private key).

---

## Solution (undisclosed version)

To renew the certificate, I generate a new self-signed key/certificate pair with `openssl`.

I then replace the SSL files used by Nginx.

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout <ssl_key_path> \
  -out <ssl_certificate_path>
```

When generating, `openssl` asks me for the "Distinguished Name" (DN).

I provide values ​​consistent with the server (country, organization, host CN), without publishing the exact game here.

Once the files are generated, I restart Nginx to support the new certificate:

```bash
sudo systemctl restart nginx
```

---

## Verification

I verify that the certificate is loaded and valid by using `openssl s_client` to connect locally to the server and inspect the served certificate.

**Date check:**
```bash
echo | openssl s_client -connect <host>:443 2>/dev/null | openssl x509 -noout -dates
```
*Expected result: `notBefore` must be recent and `notAfter` must be later.*

**Topic check:**
```bash
echo | openssl s_client -connect <host>:443 2>/dev/null | openssl x509 -noout -subject
```

If the dates are correct and Nginx restarts without errors, the correction is validated.

---

## Demonstrated skills

- **OpenSSL**: Generation of self-signed certificates (req, x509).
- **Nginx**: Localization of the SSL configuration and restart of the service.
- **Troubleshooting**: Checking the validity of a certificate on the command line.