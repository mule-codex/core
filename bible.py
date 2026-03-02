import requests
from rich import print
import os
import difflib

# -------------------------
# Config
# -------------------------

CACHE_FILE = "bible_study.txt"
STATE_FILE = "bible_state.txt"
TOTAL_VERSES = 31102
TRANSLATION = "kjv"

# -------------------------
# Book Metadata
# -------------------------

BOOKS = {
    "Genesis":"GEN","Exodus":"EXO","Leviticus":"LEV","Numbers":"NUM","Deuteronomy":"DEU",
    "Joshua":"JOS","Judges":"JDG","Ruth":"RUT",
    "1 Samuel":"1SA","2 Samuel":"2SA","1 Kings":"1KI","2 Kings":"2KI",
    "1 Chronicles":"1CH","2 Chronicles":"2CH",
    "Ezra":"EZR","Nehemiah":"NEH","Esther":"EST",
    "Job":"JOB","Psalms":"PSA","Proverbs":"PRO","Ecclesiastes":"ECC","Song of Solomon":"SNG",
    "Isaiah":"ISA","Jeremiah":"JER","Lamentations":"LAM","Ezekiel":"EZK","Daniel":"DAN",
    "Hosea":"HOS","Joel":"JOL","Amos":"AMO","Obadiah":"OBA","Jonah":"JON",
    "Micah":"MIC","Nahum":"NAM","Habakkuk":"HAB","Zephaniah":"ZEP",
    "Haggai":"HAG","Zechariah":"ZEC","Malachi":"MAL",
    "Matthew":"MAT","Mark":"MRK","Luke":"LUK","John":"JHN","Acts":"ACT",
    "Romans":"ROM","1 Corinthians":"1CO","2 Corinthians":"2CO","Galatians":"GAL",
    "Ephesians":"EPH","Philippians":"PHP","Colossians":"COL",
    "1 Thessalonians":"1TH","2 Thessalonians":"2TH",
    "1 Timothy":"1TI","2 Timothy":"2TI","Titus":"TIT","Philemon":"PHM",
    "Hebrews":"HEB","James":"JAS","1 Peter":"1PE","2 Peter":"2PE",
    "1 John":"1JN","2 John":"2JN","3 John":"3JN","Jude":"JUD","Revelation":"REV"
}

BOOK_INDEX = {abbr: i for i, abbr in enumerate(BOOKS.values())}

# -------------------------
# State Machine
# -------------------------

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


# -------------------------
# Cache
# -------------------------

def load_cache():
    cache = {}
    if not os.path.exists(CACHE_FILE):
        return cache

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if "|" not in line:
                continue
            ref, text = line.strip().split("|", 1)
            cache[ref.strip()] = text.strip()
    return cache


def save_cache(cache):
    def sort_key(ref):
        book, rest = ref.split(" ", 1)
        chapter, verse = rest.split(":")
        return (BOOK_INDEX.get(book, 999), int(chapter), int(verse))

    sorted_refs = sorted(cache.keys(), key=sort_key)

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        for ref in sorted_refs:
            f.write(f"{ref} | {cache[ref]}\n")


def update_progress(cache):
    percent = (len(cache) / TOTAL_VERSES) * 100
    print(f"\n[bold green]Verses Read:[/bold green] {len(cache)}")
    print(f"[bold green]Progress:[/bold green] {percent:.2f}%\n")


# -------------------------
# Utilities
# -------------------------

def normalize_book_name(user_input):
    names = list(BOOKS.keys())
    match = difflib.get_close_matches(user_input, names, n=1, cutoff=0.6)
    return match[0] if match else None


def fetch_reference(book_name, chapter, verse=None):
    query = f"{book_name} {chapter}:{verse}" if verse else f"{book_name} {chapter}"
    url = f"https://bible-api.com/{query}?translation={TRANSLATION}"

    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None


def parse_data(data):
    verses = {}
    if not data or "verses" not in data:
        return verses

    reference_book = data["reference"].split()[0]
    book_abbr = BOOKS.get(reference_book)

    for v in data["verses"]:
        chap = str(v["chapter"])
        verse = str(v["verse"])
        text = v["text"].strip()
        ref = f"{book_abbr} {chap}:{verse}"
        verses[ref] = text

    return verses


# -------------------------
# Reading Logic (Modified)
# -------------------------

def read_passage(book_name, chapter, verse, cache):
    state = load_state()
    book_abbr = BOOKS[book_name]

    # ---------------- SINGLE VERSE ----------------
    if verse:
        ref_key = f"{book_abbr} {chapter}:{verse}"

        if ref_key in cache:
            print(f"\n[bold]{book_name} {chapter}:{verse}[/bold]")
            print(cache[ref_key])
            state["last_reference"] = ref_key
            save_state(state)
            return

        data = fetch_reference(book_name, chapter, verse)
        if not data:
            print("Reference not found")
            return

        verses = parse_data(data)
        if ref_key in verses:
            print(f"\n[bold]{book_name} {chapter}:{verse}[/bold]")
            print(verses[ref_key])
            cache[ref_key] = verses[ref_key]
            state["last_reference"] = ref_key
            save_state(state)
        else:
            print("Verse not found")

    # ---------------- FULL CHAPTER ----------------
    else:
        print(f"\n[bold]{book_name} {chapter}[/bold]\n")

        # Print cached verses first
        chapter_refs = [
            ref for ref in cache
            if ref.startswith(f"{book_abbr} {chapter}:")
        ]

        printed_any = False

        if chapter_refs:
            for ref_key in sorted(chapter_refs, key=lambda x: int(x.split(":")[1])):
                verse_num = ref_key.split(":")[1]
                print(f"[cyan]{verse_num}[/cyan] {cache[ref_key]}")
                printed_any = True

        # Fetch missing verses from API
        data = fetch_reference(book_name, chapter)
        if data:
            verses = parse_data(data)
            for ref_key in sorted(verses.keys(), key=lambda x: int(x.split(":")[1])):
                if ref_key not in cache:
                    verse_num = ref_key.split(":")[1]
                    print(f"[cyan]{verse_num}[/cyan] {verses[ref_key]}")
                    cache[ref_key] = verses[ref_key]
                    printed_any = True

            if verses:
                state["last_reference"] = list(verses.keys())[-1]
                save_state(state)

        if not printed_any:
            print("Chapter not found")


# -------------------------
# CLI
# -------------------------

def help_menu():
    print("""
Enter references like:

Genesis 1
Genesis 1 1
John 3 16
1 John 2 1

Other commands:
books
progress
help
exit
""")


def list_books():
    print("\n[bold]Books of the Bible[/bold]\n")
    for name in BOOKS.keys():
        print(name)


def main():
    cache = load_cache()
    state = load_state()

    print("[bold cyan]Bible Study CLI[/bold cyan]")

    if "last_reference" in state:
        print(f"[dim]Last read: {state['last_reference']}[/dim]\n")

    help_menu()

    while True:
        cmd = input("\n> ").strip()

        if not cmd:
            continue

        if cmd.lower() == "exit":
            save_cache(cache)
            return

        if cmd.lower() == "help":
            help_menu()
            continue

        if cmd.lower() == "books":
            list_books()
            continue

        if cmd.lower() == "progress":
            update_progress(cache)
            continue

        tokens = cmd.split()

        chapter = None
        verse = None
        book_parts = []

        for token in tokens:
            if token.isdigit():
                if not chapter:
                    chapter = token
                else:
                    verse = token
            else:
                book_parts.append(token)

        book_input = " ".join(book_parts)
        corrected = normalize_book_name(book_input)

        if not corrected:
            print("Book not recognized")
            continue

        if not chapter:
            print("Chapter required")
            continue

        read_passage(corrected, chapter, verse, cache)
        save_cache(cache)
        update_progress(cache)


if __name__ == "__main__":
    main()