---
title: "Saint John: What is Writing to this Log File?"
date: 2026-01-24
image: "/img/banners/sadservers.png"
draft: false
reading_time: 10
categories: ["SadServers", "Linux"]
tags: ["lsof", "process", "troubleshooting", "Easy"]
---

{{< sadservers-scenario slug="saint-john" >}}

---

## Context

A log file `/var/log/bad.log` continually grows on the system. You need to identify which process is writing to it and stop it **without deleting** the source file or script.

---

## Environment / Setup

- **Machine**: VM SadServers (Ubuntu/Debian)
- **User**: `admin` (with sudo access)
- **Target file**: `/var/log/bad.log`

---

## Analysis (method)

### 1. Identify the process that is writing to the file

The `lsof` (LiSt Open Files) command lists all files open on the system, including those currently being written.

```bash
sudo lsof /var/log/bad.log
```

**Result**:
```
COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME
[process_identifie] [PID] admin 3w REG ... /var/log/bad.log
```

**Analysis**:
- **COMMAND**: `[processus_identifie]` → process responsible for writing
- **PID**: `[PID]` → process identifier
- **USER**: `admin` → the owner user
- **FD**: `3w` → File Descriptor 3 in **write** mode (writing)
- **TYPE**: `REG` → regular file

We deduce that the identified process (PID found with `lsof`) writes in `/var/log/bad.log`.

### 2. Stop the process

To stop the process without deleting the Python file, we use the `kill` command with the PID:

```bash
sudo kill <PID_IDENTIFIED>
```

This command sends a `SIGTERM` (graceful termination) signal to process 587.

### 3. Verification

To confirm that the process is stopped and the file is no longer growing:

```bash
tail -f /var/log/bad.log
```

If no new lines appear, the process is terminated successfully.

---

## Notes

- **`lsof`**: Very powerful command for system troubleshooting. It allows you to see which processes have which files open.
- **`kill` vs `kill -9`**: 
  - `kill <PID>` sends SIGTERM (clean shutdown)
  - `kill -9 <PID>` sends SIGKILL (forced shutdown, to be used as a last resort)
- **Alternatives**:
  - `fuser /var/log/bad.log`: Another method to identify processes using a file
  - `ps aux | grep badlog`: To check if the process is still active

---

## Result

✅ Process identified via `lsof`  
✅ Process stopped with `sudo kill <PID_IDENTIFIE>`  
✅ File `/var/log/bad.log` no longer grows  
✅ **Challenge validated on SadServers.**

---

## Demonstrated skills

- Using `lsof` to identify open files
- Understanding of Linux processes and PIDs
- Process management with `kill`
- Linux system troubleshooting