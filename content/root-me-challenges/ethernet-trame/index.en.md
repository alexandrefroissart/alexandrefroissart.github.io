---
title: "ETHERNET - Trame"
date: 2026-01-24
image: "/img/banners/rootme-banner.png"
draft: false
rootme_id: 336
categories: ["Root-Me", "Réseau"]
tags: ["Ethernet", "Wireshark", "Base64", "HTTP", "Facile"]
---

{{< rootme-challenge slug="ethernet-trame" >}}

---

## Context

This challenge consists of analyzing a raw Ethernet frame provided in hexadecimal.  
The objective is to identify sensitive information transmitted, including HTTP Basic authentication.

---

## Environment / Setup

- **Machine**: VM Debian (XFCE) on VMware Fusion (MacBook Pro M1 Pro)
- **User**: `alex`
- **Tools**: CyberChef, online Base64 decoder

### Data provided

```
[Raw frame provided by the statement - full value not reproduced here]
```

---

## Analysis (method)

### 1. Hexadecimal → ASCII conversion

By converting the hexadecimal frame to ASCII, we can identify the HTTP request:

```
GET/HTTP/1.1
Authorization: Basic [REDACTED_BASE64]
User-Agent: InsaneBrowser
Host: www.myipv6.org
Accept: */*
```

### 2. Identifying HTTP Basic Authentication

The key line is:
```
Authorization: Basic [REDACTED_BASE64]
```

**HTTP Basic** authentication encodes credentials in `username:password` format in **Base64**.

### 3. Base64 decoding

The string `Y29uZmk6ZGVudGlhbA==` ends with two `==` signs, which is characteristic of Base64 encoding.

Decoding:
```
[REDACTED_BASE64] → [username]:[password]
```

**Result**:
- Username: `[REDACTED]`
- Password: `[REDACTED]`

The exact identifiers are deliberately hidden to respect the confidentiality of the challenges.

---

## Notes

- **HTTP Basic Auth**: This authentication mechanism transmits credentials in plain text (Base64 encoded, but **not encrypted**). This is why it is dangerous without HTTPS.
- **Base64**: Base64 encoding is often recognized by:
  - Alphanumeric characters + `+` and `/`
  - Ending with `=` or `==` (padding)
- **Useful tools**:
  - CyberChef (https://gchq.github.io/CyberChef/)
  - Online Base64 decoders
  - echo "Y29uZmk6ZGVudGlhbA==" | base64 -d` (command line)

---

## Result

✅ I identified the HTTP request in the Ethernet frame.  
✅ I decoded Basic authentication to Base64.  
✅ **Challenge validated on Root-Me.**

---

## Demonstrated skills

- Reading and analysis of raw network frames (hexadecimal)
- Understanding of HTTP protocol and Basic authentication
- Base64 decoding
- Detection of sensitive information in network traffic