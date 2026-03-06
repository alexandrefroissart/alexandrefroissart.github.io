---
title: "FTP - Authentification"
date: 2026-01-23
image: "/img/banners/rootme-banner.png"
draft: false
rootme_id: 96
categories: ["Root-Me", "Réseau"]
tags: ["FTP", "Wireshark", "PCAP", "Facile"]
---

{{< rootme-challenge slug="ftp-authentification" >}}

This capture shows a classic case: an FTP service without encryption lets `USER` and `PASS` pass in plain text.

The work mainly consists of quickly going to the right packets, then properly confirming what the flow reveals.

## Environment

- **Machine**: VM Debian (XFCE) on VMware Fusion (MacBook Pro M1 Pro)
- **User**: `alex`
- **Tool**: Wireshark

### Installation and minimum hygiene

```bash
sudo apt-get update
sudo apt-get -y install wireshark
```

During installation, Debian asks:

> "Should non-superusers be able to capture packets?"
> ➡️ **Answer: No**

I leave the capture reserved for `root` to maintain least privilege logic.

## Approach

### 1. Open capture

I open `Downloads/ch1.pcap` in Wireshark.

### 2. Target the authentication phase

In Wireshark:

- I filter on FTP traffic;
- I locate the authentication sequence;
- I am looking for the `USER` then `PASS` commands.

### 3. Confirm in package detail

I then check in the bottom panel for the exact FTP command sent by the client.

## Observations

- I identify the user sent via `USER`:
  - **USER** = `[REDACTED]` *(value deliberately hidden)*
- The password is present in the `PASS` command:
  - **PASS** = `[REDACTED]` *(value deliberately hidden)*

## Result

✅ I located the FTP identifiers in the network capture application flow.  
✅ **Challenge validated on Root-Me.**

## What I remember

- Clear FTP remains very simple to audit in a network capture.
- Wireshark allows you to move quickly if you first focus on the useful application sequence.
- Even on a simple exercise, I keep a logic of least privilege during the implementation.

## Skills mobilized

- PCAP analysis with Wireshark
- Reading the FTP protocol and its authentication in plain text
- Extraction of information at the application level
- Hygiene safety during installation and capture
