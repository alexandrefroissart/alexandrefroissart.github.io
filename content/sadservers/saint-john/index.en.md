---
title: "Saint John: What is Writing to this Log File?"
date: 2026-01-24
image: "/img/banners/sadservers.png"
draft: false
reading_time: 10
categories: ["SadServers", "Linux"]
tags: ["lsof", "process", "troubleshooting", "Easy"]
context: "SadServers troubleshooting scenario around a log file that keeps growing in the background."
objective: "Identify which process is writing to the log without touching the source script, then stop it cleanly."
tools:
  - "lsof"
  - "kill"
  - "tail"
---

{{< sadservers-scenario slug="saint-john" >}}

Here, the problem is simple but very realistic: a file `/var/log/bad.log` grows continuously, and you have to identify the process responsible without touching either the file or the source script.

## Environment

- **Machine**: VM SadServers (Ubuntu/Debian)
- **User**: `admin` (with sudo access)
- **Target file**: `/var/log/bad.log`

## Approach

### 1. Identify the process that is writing to the file

The `lsof` command lists open files on the system, including those currently being written.

```bash
sudo lsof /var/log/bad.log
```

**Result**:
```
COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME
[identified_process] [PID] admin 3w REG ... /var/log/bad.log
```

- **COMMAND**: `[identified_process]` -> process responsible for writing
- **PID**: `[PID]` -> process identifier
- **USER**: `admin` -> owner user
- **FD**: `3w` -> file descriptor 3 in **write** mode
- **TYPE**: `REG` → regular file

The process found with `lsof` is therefore the one which writes to `/var/log/bad.log`.

### 2. Stop the process properly

To stop it without deleting the Python file, I use `kill` with the PID marked just before:

```bash
sudo kill <PID_IDENTIFIED>
```

This command sends a `SIGTERM` signal, therefore a clean termination, to the identified process.

### 3. Verify that writing stops

To confirm that the process is stopped and that the file is no longer growing:

```bash
tail -f /var/log/bad.log
```

If no new lines appear, the correction is good.

## What I remember

- `lsof` is a very good reflex for system troubleshooting when a file grows or remains locked.
- I start with `SIGTERM` before considering a `kill -9`, because a clean shutdown is always better.
- `fuser /var/log/bad.log` would also have made it possible to quickly identify the process.

## Result

✅ Process identified via `lsof`  
✅ Process stopped with `sudo kill <PID_IDENTIFIE>`  
✅ File `/var/log/bad.log` no longer grows  
✅ **Challenge validated on SadServers.**

## Skills mobilized

- Using `lsof` to identify open files
- Understanding of Linux processes and PIDs
- Process management with `kill`
- Linux system troubleshooting
