---
title: "ETHERNET - Frame"
date: 2026-01-24
image: "/img/banners/rootme-banner.png"
draft: false
categories: ["Root-Me", "Network"]
tags: ["Ethernet", "Wireshark", "Base64", "HTTP", "Easy"]
---

{{< rootme-challenge slug="ethernet-trame" >}}

---

## Context

This challenge involves analyzing a raw Ethernet frame provided in hexadecimal format.  
The goal is to identify sensitive information transmitted, particularly HTTP Basic authentication.

---

## Environment / Setup

- **Machine**: Debian VM (XFCE) on VMware Fusion (MacBook Pro M1 Pro)
- **User**: `alex`
- **Tools**: CyberChef, online Base64 decoder

### Provided Data

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

### 1. Hexadecimal → ASCII Conversion

Converting the hexadecimal frame to ASCII reveals the HTTP request:

```
GET / HTTP/1.1
Authorization: Basic Y29uZmk6ZGVudGlhbA==
User-Agent: InsaneBrowser
Host: www.myipv6.org
Accept: */*
```

### 2. HTTP Basic Authentication Identification

The key line is:
```
Authorization: Basic Y29uZmk6ZGVudGlhbA==
```

**HTTP Basic** authentication encodes credentials in `username:password` format using **Base64**.

### 3. Base64 Decoding

The string `Y29uZmk6ZGVudGlhbA==` ends with two `==` signs, which is characteristic of Base64 encoding.

Decoding:
```
Y29uZmk6ZGVudGlhbA== → confi:dential
```

**Result**:
- Username: `confi`
- Password: `dential`

The expected password for the challenge is: **`dential`**

---

## Comments

- **HTTP Basic Auth**: This authentication mechanism transmits credentials in clear text (Base64 encoded, but **not encrypted**). This is why it's dangerous without HTTPS.
- **Base64**: Base64 encoding can be recognized by:
  - Alphanumeric characters + `+` and `/`
  - Ending with `=` or `==` (padding)
- **Useful tools**:
  - CyberChef (https://gchq.github.io/CyberChef/)
  - Online Base64 decoders
  - `echo "Y29uZmk6ZGVudGlhbA==" | base64 -d` (command line)

---

## Result

✅ I identified the HTTP request in the Ethernet frame.  
✅ I decoded the Basic authentication from Base64.  
✅ **Challenge validated on Root-Me.**

---

## Demonstrated skills

- Reading and analyzing raw network frames (hexadecimal)
- Understanding HTTP protocol and Basic authentication
- Base64 decoding
- Detecting sensitive information in network traffic
