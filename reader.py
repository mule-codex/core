import sys
import os
import curses
import threading
import time
from pypdf import PdfReader

PDF_DIR = os.path.join("downloads", "pdf")
BOOKS_DIR = os.path.join("books")
STATE_FILE = os.path.join("books", "reader_state.txt")


# ================= DIRECTORIES =================

def ensure_directories():
    os.makedirs(PDF_DIR, exist_ok=True)
    os.makedirs(BOOKS_DIR, exist_ok=True)


# ================= SPINNER =================

def spinner(stop_event):
    frames = ["/", "-", "\\", "|"]
    i = 0
    while not stop_event.is_set():
        frame = frames[i % len(frames)]
        sys.stdout.write(f"\rimporting pdf {frame}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write("\r" + " " * 30 + "\r")
    sys.stdout.flush()


# ================= STATE =================

def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    state = {}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                state[k] = v
    return state


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        for k, v in state.items():
            f.write(f"{k}={v}\n")


# ================= PDF SELECTION =================

def select_pdf_from_directory():
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print(f"No PDF files found in {PDF_DIR}")
        sys.exit(1)

    print(f"\nAvailable PDFs in {PDF_DIR}:\n")
    for idx, filename in enumerate(pdf_files, 1):
        print(f"{idx}. {filename}")

    while True:
        choice = input("\nSelect PDF number: ").strip()
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(pdf_files):
                return os.path.join(PDF_DIR, pdf_files[index])
        print("Invalid selection.")


# ================= CACHE LOADING =================

def cache_path_for(pdf_path):
    name = os.path.splitext(os.path.basename(pdf_path))[0]
    return os.path.join(BOOKS_DIR, f"{name}.txt")


def load_from_cache(cache_path):
    pages = []
    with open(cache_path, "r", encoding="utf-8") as f:
        content = f.read()
    pages = content.split("\n===PAGE_BREAK===\n")
    return pages


def save_to_cache(cache_path, pages):
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write("\n===PAGE_BREAK===\n".join(pages))


def extract_pdf_text(pdf_path):
    reader = PdfReader(pdf_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        pages.append(text if text else "[No extractable text]")
    return pages


def load_pdf_text(pdf_path):
    cache_path = cache_path_for(pdf_path)

    if os.path.exists(cache_path):
        return load_from_cache(cache_path)

    stop_event = threading.Event()
    spin_thread = threading.Thread(target=spinner, args=(stop_event,))
    spin_thread.start()

    try:
        pages = extract_pdf_text(pdf_path)
        save_to_cache(cache_path, pages)
    finally:
        stop_event.set()
        spin_thread.join()

    return pages


# ================= DISPLAY =================

def display_page(stdscr, text, page_num, total_pages):
    stdscr.clear()
    height, width = stdscr.getmaxyx()

    header = f"Page {page_num + 1}/{total_pages}  |  n: next  p: prev  q: quit"
    stdscr.addstr(0, 0, header[:width - 1])

    lines = text.split("\n")
    for i, line in enumerate(lines):
        if i + 2 >= height:
            break
        stdscr.addstr(i + 2, 0, line[:width - 1])

    stdscr.refresh()


# ================= MAIN =================

def main(stdscr, pdf_path):
    curses.curs_set(0)

    state = load_state()
    book_key = os.path.basename(pdf_path)

    pages = load_pdf_text(pdf_path)
    total_pages = len(pages)

    # Restore last page if exists
    current_page = int(state.get(book_key, 0))
    current_page = min(current_page, total_pages - 1)

    while True:
        display_page(stdscr, pages[current_page], current_page, total_pages)
        key = stdscr.getch()

        if key == ord('n') and current_page < total_pages - 1:
            current_page += 1
        elif key == ord('p') and current_page > 0:
            current_page -= 1
        elif key == ord('q'):
            state[book_key] = str(current_page)
            save_state(state)
            break


# ================= ENTRY =================

if __name__ == "__main__":
    ensure_directories()

    if len(sys.argv) == 2:
        pdf_path = sys.argv[1]
    else:
        pdf_path = select_pdf_from_directory()

    curses.wrapper(main, pdf_path)