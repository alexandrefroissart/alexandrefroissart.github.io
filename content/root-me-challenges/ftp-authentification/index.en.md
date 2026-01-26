---
title: "FTP - Authentification"
date: 2026-01-23
image: "/img/banners/rootme-banner.png"
draft: false
rootme_id: 96
categories: ["Root-Me", "Réseau"]
tags: ["FTP", "Wireshark", "PCAP", "Facile"]
---

{{< rootme-challenge slug="ftp-authentication" >}}

---

## Context

FTP transmits authentication in clear text (USER/PASS) if no encrypted layer is used.  
The goal is to identify these exchanges in a `.pcap` file.

---

## Environment / Setup

- **Machine**: VM Debian (XFCE) on VMware Fusion (MacBook Pro M1 Pro)
- **User**: `alex`
- **Tool**: Wireshark

### Installation (security)

```bash
sudo apt-get update
sudo apt-get -y install wireshark
```

During installation, Debian asks:

> "Should non-superusers be able to capture packets?"
> ➡️ **Answer: No**

**Why?** I avoid allowing network capture to non-root users (reduction of attack surface / least privilege).

---

## Analysis (method)

1. I open the capture: `Downloads/ch1.pcap`

2. In Wireshark:
   - I filter on FTP (or I identify the frames where the protocol is FTP)
   - I am looking for the FTP authentication sequence:
     - `USE ...`
     - `PASS...`

3. I check in the packet details (bottom panel) the FTP command sent.

---

## Comments

- I identify the user sent via `USER`:
  - **USER** = `cdts3500`
- The password is present in the `PASS` command:
  - **PASS** = `[REDACTED]` *(value deliberately hidden)*

---

## Result

✅ I located the FTP identifiers in the network capture application flow.  
✅ **Challenge validated on Root-Me.**

---

## Demonstrated skills

- PCAP analysis with Wireshark
- FTP protocol reading (clear authentication)
- Extraction of information on the application layer
- Hygiene and safety: least privilege during installation/capture