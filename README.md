<<<<<<< HEAD
# Jianjun Chen's Personal Page

Welcome to the personal page repository for jianjun_chen. 

## Overview
This repository contains a simple, visually appealing single-page personal website that displays:
- The name of the user: **jianjun_chen**
- An accurate timestamp showing the creation time.

## Technologies
- **HTML5:** Defines the simple web structure.
- **CSS3:** Includes styling such as typography, colors, soft shadows, and hover animations to give the page a clean, modern aesthetic.

## Usage
Simply clone this repository and open the `index.html` file in any modern web browser to view the page.
=======
# Personal Web Page & Utility Scripts (Jianjun Chen)

This repository/folder contains a collection of custom scripts and a motion-rich personal web page created for Jianjun Chen.

## 🌟 1. Motion Personal Web Page (`jianjun_chen.html`)
A modern, dynamic, and aesthetic personal landing page built using pure HTML, CSS, and JavaScript. 

### Features:
- **Real-Time Digital Clock**: Fetches your local system time and updates every single second.
- **Contextual Greetings**: Automatically detects the time of day and greets you with "Good Morning", "Good Afternoon", "Good Evening", or "Good Night".
- **Glassmorphism Design**: Uses blurred, frosted-glass effects (backdrop-filter) to create a premium visual experience.
- **Ambient Animations**: Drifting gradient orbs in the background create a soothing, motion-rich atmosphere.
- **Interactive UI**: Soft hover effects that elevate the card to make it feel responsive and alive.

### How to Use:
Simply double-click on `jianjun_chen.html` to open it in any modern web browser (Google Chrome, Microsoft Edge, Firefox, etc.). No server or internet connection is required to run the core logic (only to load the Google Font).

---

## 🛠️ 2. Windows Process Monitors (C++)
This directory also contains a set of custom Windows Process Monitor tools built in C/C++, ranging from a snapshot tool to an exact UI clone of Sysinternals ProcMon.

### Files Included:
- **`ProcessMonitor.cpp`**: 
  A standard command-line utility that takes a static snapshot of all currently running processes utilizing the standard Windows `Toolhelp32` API. It includes advanced features like memory tracking (`psapi.h`) and parent PIDs.
- **`RealTimeProcMon.cpp`**: 
  An advanced command-line tool that acts like Sysinternals ProcMon. It uses WMI to subscribe to real-time `__InstanceCreationEvent` streams, printing immediately when a process is spawned.
- **`MiniProcMon.cpp`**: 
  A fully native Win32 GUI clone of Sysinternals Process Monitor. It features a scalable `SysListView32` UI, live start/stop capture buttons, and multithreaded Event Tracing for Windows (WMI).

### How to Compile (Process Monitors):
These programs use native Microsoft Windows libraries (such as `Wbemidl.h` for COM/WMI). It is recommended to use the **Microsoft Visual C++ Compiler (MSVC)**.

Open the **Developer Command Prompt for VS**, navigate to this folder, and run:
```cmd
cl MiniProcMon.cpp
MiniProcMon.exe
```

---
*Created dynamically for Jianjun Chen.*
>>>>>>> 1c4bea5 (Add personal page and README)
