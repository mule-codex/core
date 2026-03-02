import csv
import os
from datetime import datetime, date, timedelta

CSV_FILE = "habits_data.csv"
STATE_FILE = "habits_state.txt"

FIELDNAMES = [
    "habit",
    "type",
    "unit",
    "date",
    "value",
    "context",
    "notes",
    "created_at"
]


# ================= STATE MACHINE =================

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    state = {}
    with open(STATE_FILE, "r") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                state[k] = v
    return state


def save_state(state):
    with open(STATE_FILE, "w") as f:
        for k, v in state.items():
            f.write(f"{k}={v}\n")


# ================= STORAGE =================

def initialize():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def read_all():
    initialize()
    with open(CSV_FILE, "r", newline="") as f:
        return list(csv.DictReader(f))


def write_all(rows):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


# ================= HABIT CORE =================

def get_habits(rows):
    return sorted(set(r["habit"] for r in rows if r["date"] == ""))


def get_habit_info(rows, habit):
    for r in rows:
        if r["habit"] == habit and r["date"] == "":
            return r["type"], r["unit"]
    return None, None


def register_habit(rows):
    name = input("Habit name: ").strip().lower()
    if not name:
        print("Invalid name.")
        return rows

    if name in get_habits(rows):
        print("Habit already exists.")
        return rows

    habit_type = input("Type (good = build / bad = quit): ").strip().lower()
    if habit_type not in ["good", "bad"]:
        print("Invalid type.")
        return rows

    unit = input("Measurement unit: ").strip().lower() or "count"

    rows.append({
        "habit": name,
        "type": habit_type,
        "unit": unit,
        "date": "",
        "value": "0",
        "context": "meta",
        "notes": "registered",
        "created_at": datetime.utcnow().isoformat()
    })

    write_all(rows)

    state = load_state()
    state["last_command"] = "register"
    state["last_habit"] = name
    save_state(state)

    print("Habit registered.\n")
    return rows


# ================= LOGGING =================

def log_event(rows):
    habits = get_habits(rows)
    if not habits:
        print("No habits registered.")
        return rows

    print("Habits:", ", ".join(habits))
    habit = input("Habit name: ").strip().lower()

    if habit not in habits:
        print("Habit not found.")
        return rows

    habit_type, unit = get_habit_info(rows, habit)
    today_str = date.today().isoformat()

    if habit_type == "good":
        value_input = input(f"How many {unit} today? ").strip()
        value = int(value_input) if value_input.isdigit() else 0
        context = input("Context: ").strip()
    else:
        value_input = input("Relapse count (default 1): ").strip()
        value = int(value_input) if value_input.isdigit() else 1
        context = input("Trigger/context: ").strip()

    notes = input("Optional notes: ").strip()

    rows.append({
        "habit": habit,
        "type": habit_type,
        "unit": unit,
        "date": today_str,
        "value": str(value),
        "context": context,
        "notes": notes,
        "created_at": datetime.utcnow().isoformat()
    })

    write_all(rows)

    state = load_state()
    state["last_command"] = "log"
    state["last_habit"] = habit
    save_state(state)

    print("Entry logged.\n")
    return rows


# ================= METRICS =================

def compute_metrics(rows, habit):
    habit_type, unit = get_habit_info(rows, habit)

    logs = [r for r in rows if r["habit"] == habit and r["date"] != ""]
    total = sum(int(r["value"]) for r in logs)

    today = date.today()
    date_map = {}

    for r in logs:
        date_map.setdefault(r["date"], 0)
        date_map[r["date"]] += int(r["value"])

    streak = 0
    pointer = today

    while True:
        key = pointer.isoformat()

        if habit_type == "good":
            condition = key in date_map and date_map[key] > 0
        else:
            condition = key not in date_map or date_map[key] == 0

        if condition:
            streak += 1
        else:
            break

        pointer -= timedelta(days=1)
        if pointer < today - timedelta(days=3650):
            break

    longest = 0
    current = 0

    if logs:
        start = min(datetime.strptime(r["date"], "%Y-%m-%d").date() for r in logs)
        pointer = start

        while pointer <= today:
            key = pointer.isoformat()

            if habit_type == "good":
                condition = key in date_map and date_map[key] > 0
            else:
                condition = key not in date_map or date_map[key] == 0

            if condition:
                current += 1
                longest = max(longest, current)
            else:
                current = 0

            pointer += timedelta(days=1)

    return total, streak, longest, unit


def show_dashboard(rows):
    habits = get_habits(rows)

    if not habits:
        print("\nNo habits registered.\n")
        return

    state = load_state()
    state["last_command"] = "dashboard"
    save_state(state)

    print("\n=========== DASHBOARD ===========")

    for habit in habits:
        habit_type, unit = get_habit_info(rows, habit)
        total, streak, longest, unit = compute_metrics(rows, habit)

        print(f"\nHabit: {habit} ({habit_type})")

        if habit_type == "good":
            print(f"  Total Progress: {total} {unit}")
        else:
            print(f"  Total Relapses: {total}")

        print(f"  Current Streak: {streak} day(s)")
        print(f"  Longest Streak: {longest} day(s)")

    print("\n=================================\n")


# ================= HELP =================

def show_help():
    print("""
COMMANDS:
register   - Create new habit
log        - Log progress or relapse
dashboard  - View metrics
help       - Show help
exit       - Quit
""")


# ================= MAIN =================

def main():
    initialize()
    state = load_state()

    print("Habits Tracker")

    if "last_command" in state:
        print(f"(Last action: {state['last_command']})")
        if "last_habit" in state:
            print(f"(Last habit: {state['last_habit']})")

    show_help()

    while True:
        command = input("\nCommand: ").strip().lower()
        rows = read_all()

        if command == "register":
            rows = register_habit(rows)

        elif command == "log":
            rows = log_event(rows)

        elif command == "dashboard":
            show_dashboard(rows)

        elif command == "help":
            show_help()

        elif command == "exit":
            print("Exiting.")
            return

        else:
            print("Unknown command. Type 'help'.")


if __name__ == "__main__":
    main()