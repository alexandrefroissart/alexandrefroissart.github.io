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
00 05 73 a0 00 00 e0 69 95 d8 5a 13 86 dd 60 00
00 00 00 9b 06 40 26 07 53 00 00 60 2a bc 00 00
00 00 ba de c0 de 20 01 41 d0 00 02 42 33 00 00
00 00 00 00 00 04 96 74 00 50 bc ea 7d b8 00 c1
d7 03 80 18 00 e1 cf a0 00 00 01 01 08 0a 09 3e
69 b9 17 a1 7e d3 47 45 54 20 2f 20 48 54 54 50
2f 31 2e 31 0d 0a 41 75 74 68 6f 72 69 7a 61 74
69 6f 6e 3a 20 42 61 73 69 63 20 59 32 39 75 5a
6d 6b 36 5a 47 56 75 64 47 6c 68 62 41 3d 3d 0d
0a 55 73 65 72 2d 41 67 65 6e 74 3a 20 49 6e 73
61 6e 65 42 72 6f 77 73 65 72 0d 0a 48 6f 73 74
3a 20 77 77 77 2e 6d 79 69 70 76 36 2e 6f 72 67
0d 0a 41 63 63 65 70 74 3a 20 2a 2f 2a 0d 0a 0d
0a
```

---

## Analysis (method)

### 1. Hexadecimal → ASCII conversion

By converting the hexadecimal frame to ASCII, we can identify the HTTP request:

```
GET/HTTP/1.1
Authorization: Basic Y29uZmk6ZGVudGlhbA==
User-Agent: InsaneBrowser
Host: www.myipv6.org
Accept: */*
```

### 2. Identifying HTTP Basic Authentication

The key line is:
```
Authorization: Basic Y29uZmk6ZGVudGlhbA==
```

**HTTP Basic** authentication encodes credentials in `username:password` format in **Base64**.

### 3. Base64 decoding

The string `Y29uZmk6ZGVudGlhbA==` ends with two `==` signs, which is characteristic of Base64 encoding.

Decoding:
```
Y29uZmk6ZGVudGlhbA== → confi:dential
```

**Result**:
- Username: `confi`
- Password: `dential`

The password expected by the challenge is: **`dential`**

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