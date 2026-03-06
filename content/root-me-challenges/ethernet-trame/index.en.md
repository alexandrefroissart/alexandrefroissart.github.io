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

This challenge requires starting from a raw Ethernet frame in hexadecimal to find the sensitive information it carries.

The important point here is HTTP Basic authentication visible directly in the payload.

## Environment

- **Machine**: VM Debian (XFCE) on VMware Fusion (MacBook Pro M1 Pro)
- **User**: `alex`
- **Tools**: CyberChef, online Base64 decoder

## Data provided

```
[Raw frame provided by the statement - full value not reproduced here]
```

## Approach

### 1. Change the frame to ASCII

By converting the hexadecimal frame into ASCII, we highlight the HTTP request contained in the stream:

```
GET / HTTP/1.1
Authorization: Basic [REDACTED_BASE64]
User-Agent: InsaneBrowser
Host: www.myipv6.org
Accept: */*
```

### 2. Isolate the useful element

The line to remember is:

```
Authorization: Basic [REDACTED_BASE64]
```

**HTTP Basic** authentication simply encodes the `username:password` pair in **Base64**.

### 3. Check Base64

The string `Y29uZmk6ZGVudGlhbA==` ends with `==`, which corresponds to a Base64 encoding.

Once decoded, we find the expected format:

```
[REDACTED_BASE64] → [username]:[password]
```

**What I get**:
- Username: `[REDACTED]`
- Password: `[REDACTED]`

The exact identifiers are deliberately hidden to respect the confidentiality of the challenges.

## What I remember

- **HTTP Basic** transmits credentials in clear text. Base64 is an encoding, not an encryption.
- **Base64** is often identified by:
  - Alphanumeric characters + `+` and `/`
  - Ending with `=` or `==`
- **Practical tools**:
  - CyberChef (https://gchq.github.io/CyberChef/)
  - Online Base64 decoders
  - `echo "Y29uZmk6ZGVudGlhbA==" | base64 -d` (command line)

## Result

✅ I identified the HTTP request in the Ethernet frame.  
✅ I decoded Basic authentication to Base64.  
✅ **Challenge validated on Root-Me.**

## Skills mobilized

- Reading and analysis of raw network frames (hexadecimal)
- Understanding of HTTP protocol and Basic authentication
- Base64 decoding
- Detection of sensitive information in network traffic
