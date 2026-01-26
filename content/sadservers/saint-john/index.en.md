---
title: "Saint John: What is Writing to this Log File?"
date: 2026-01-24
image: "/img/banners/sadservers.png"
draft: false
categories: ["SadServers", "Linux"]
tags: ["lsof", "process", "troubleshooting", "Easy"]
---

{{< sadservers-scenario slug="saint-john" >}}

---

## Context

A log file `/var/log/bad.log` is continuously growing on the system. We need to identify which process is writing to it and stop it **without deleting** the file or the source script.

---

## Environment / Setup

- **Machine**: SadServers VM (Ubuntu/Debian)
- **User**: `admin` (with sudo access)
- **Target file**: `/var/log/bad.log`

---

## Analysis (method)

### 1. Identify the process writing to the file

The `lsof` command (LiSt Open Files) allows you to list all open files on the system, including those being written to.

```bash
sudo lsof /var/log/bad.log
```

**Result**:
```
COMMAND   PID  USER   FD   TYPE DEVICE SIZE/OFF   NODE NAME
badlog.py 587 admin    3w   REG  259,1    52179 265802 /var/log/bad.log
```

**Analysis**:
- **COMMAND**: `badlog.py` → a Python script
- **PID**: `587` → the process identifier
- **USER**: `admin` → the owner user
- **FD**: `3w` → File Descriptor 3 in **write** mode
- **TYPE**: `REG` → regular file

We can deduce that the `badlog.py` script (PID 587) is responsible for writing to `/var/log/bad.log`.

### 2. Stop the process

To stop the process without deleting the Python file, we use the `kill` command with the PID:

```bash
sudo kill 587
```

This command sends a `SIGTERM` signal (graceful termination) to process 587.

### 3. Verification

To confirm that the process is stopped and the file is no longer growing:

```bash
tail -f /var/log/bad.log
```

If no new lines appear, the process has been successfully stopped.

---

## Comments

- **`lsof`**: Very powerful command for system troubleshooting. It shows which processes have which files open.
- **`kill` vs `kill -9`**: 
  - `kill <PID>` sends SIGTERM (clean shutdown)
  - `kill -9 <PID>` sends SIGKILL (forced kill, use as last resort)
- **Alternatives**:
  - `fuser /var/log/bad.log`: Another method to identify processes using a file
  - `ps aux | grep badlog`: To check if the process is still active

---

## Result

✅ Process identified: `badlog.py` (PID 587)  
✅ Process stopped with `sudo kill 587`  
✅ File `/var/log/bad.log` no longer growing  
✅ **Challenge validated on SadServers.**

---

## Demonstrated skills

- Using `lsof` to identify open files
- Understanding Linux processes and PIDs
- Process management with `kill`
- Linux system troubleshooting
