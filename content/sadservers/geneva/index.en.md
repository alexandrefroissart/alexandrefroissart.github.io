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

## Solution

To renew the certificate, I generate a new self-signed key/certificate pair with `openssl`. I directly replace existing files.

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/nginx.key \
  -out /etc/nginx/ssl/nginx.crt
```

When generating, `openssl` asks me for information for the "Distinguished Name" (DN). I fill with the following values:

- **Country Name (2 letter code)**: `CH`
- **State or Province Name**: `Geneva`
- **Locality Name**: `Geneva`
- **Organization Name**: `Acme`
- **Organizational Unit Name**: `IT Department`
- **Common Name (e.g. server FQDN)**: `localhost`
- **Email Address**: (leave blank)

Once the files are generated, I restart Nginx to support the new certificate:

```bash
sudo systemctl restart nginx
```

---

## Verification

I verify that the certificate is loaded and valid by using `openssl s_client` to connect locally to the server and inspect the served certificate.

**Date check:**
```bash
echo | openssl s_client -connect localhost:443 2>/dev/null | openssl x509 -noout -dates
```
*Expected result: `notBefore` should be today's date and `notAfter` one year from now (2025).*

**Topic check:**
```bash
echo | openssl s_client -connect localhost:443 2>/dev/null | openssl x509 -noout -subject
```
*Result:*
`subject=CN = localhost, O = Acme, OU = IT Department, L = Geneva, ST = Geneva, C = CH`

Everything matches! The certificate is renewed and valid.

---

## Demonstrated skills

- **OpenSSL**: Generation of self-signed certificates (req, x509).
- **Nginx**: Localization of the SSL configuration and restart of the service.
- **Troubleshooting**: Checking the validity of a certificate on the command line.