# CORE TERMINAL

A modular command-line productivity environment composed of:

- **Bible Study CLI**
- **Habits Tracker**
- **Terminal PDF Reader (Python 3.12)**
- A supervising **Process Manager** with connectivity monitoring and signal handling

This project provides a unified terminal interface for structured reading, habit tracking, and long-form PDF study.

## Architecture Overview
core.py
├── bible.py
├── habits.py
└── reader.py

### 1. `core.py`
Orchestrator and process supervisor.

**Responsibilities**
- Service registration and lifecycle management
- Subprocess isolation
- Connectivity monitoring
- Graceful shutdown on SIGINT / SIGTERM
- Interactive service launcher menu

### 2. `bible.py`
CLI-based Bible reader with:
- API-backed verse retrieval
- Local caching
- Progress tracking
- State persistence
- Fuzzy book name matching

### 3. `habits.py`
Structured habit tracking system with:
- Habit registration (build or quit)
- Daily logging
- Streak computation
- Longest streak analysis
- CSV-backed storage
- Dashboard metrics

### 4. `reader.py`
Terminal-based PDF reader built with:
- `curses` UI
- Page caching
- State restoration per document
- Background spinner during PDF import

# Installation
## Requirements

- Python 3.10+ (default services)
- Python 3.12 (PDF reader, if using `py -3.12`)
- pip

## Dependencies

Install required packages:

bash
pip install requests rich pypdf

Windows users must have the `py` launcher available for `-3.12` support.


# Running the Project

From the root directory:


python core.py

You will see:


========== CORE TERMINAL ==========
1. Bible Study
2. Habits Tracker
3. PDF Reader (Python 3.12)
4. Exit
===================================

# Module Details


## Bible Study CLI

### Features

* Fetches verses from `https://bible-api.com`
* Translation: `KJV`
* Caches verses locally
* Tracks progress across 31,102 verses
* Remembers last reference read
* Fuzzy matching for book names

### Commands


Genesis 1
Genesis 1 1
John 3 16
1 John 2 1
books
progress
help
exit
```

### Files Generated

| File              | Purpose             |
| ----------------- | ------------------- |
| `bible_study.txt` | Cached verses       |
| `bible_state.txt` | Last read reference |



## Habits Tracker

### Habit Types

| Type | Meaning     |
| ---- | ----------- |
| good | Build habit |
| bad  | Quit habit  |

### Commands

```
register
log
dashboard
help
exit
```

### Metrics Calculated

* Total progress (good habits)
* Total relapses (bad habits)
* Current streak
* Longest streak

### Files Generated

| File               | Purpose                   |
| ------------------ | ------------------------- |
| `habits_data.csv`  | Event log + metadata      |
| `habits_state.txt` | Last command + last habit |

---

## Terminal PDF Reader

### Features

* Loads PDFs from:
  downloads/pdf/

* Extracts and caches pages to:

  ```
  books/<filename>.txt
  ```
* Persists last read page per document
* Keyboard navigation:

| Key | Action        |
| --- | ------------- |
| n   | Next page     |
| p   | Previous page |
| q   | Quit          |

### State File

```
books/reader_state.txt
```

# Process Management

The `ProcessManager`:

* Launches services as isolated subprocesses
* Waits for exit codes
* Logs abnormal termination
* Terminates all children on shutdown

The `ConnectivityMonitor`:

* Pings Google every 5 seconds
* Logs connectivity loss

# Logging

All logs written to:

```
core.log
```

Includes:

* Service lifecycle events
* Errors
* Connectivity warnings
* Signal handling events

# Directory Structure

```
project/
│
├── core.py
├── bible.py
├── habits.py
├── reader.py
├── core.log
│
├── downloads/
│   └── pdf/
│
├── books/
│   └── reader_state.txt
│
├── bible_study.txt
├── bible_state.txt
├── habits_data.csv
└── habits_state.txt
```
# Design Principles

* Subprocess isolation for fault containment
* File-based persistence (no database dependency)
* Deterministic caching
* Stateful CLI workflows
* Modular service registration
* Clean shutdown behavior

# Extending the System

To add a new service:

1. Create a new Python module.
2. Register it in `core.py`:

```python
manager.register(
    "new_service",
    Service("New Service", [PYTHON_DEFAULT, NEW_PATH])
)
 

3. Add a menu option.



# Operational Notes

* Bible API requires internet connection.
* Connectivity monitor does not block execution.
* PDF extraction may take time on first load (cached afterward).
* Streak calculations assume daily usage consistency.

# Summary

This project provides:

* Structured scripture study
* Quantified habit formation tracking
* Terminal-based long-form reading
* Centralized process orchestration 
