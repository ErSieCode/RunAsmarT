import threading
import time
import tkinter as tk
import re
import os
from tkinter import ttk, scrolledtext, messagebox, filedialog

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager


def get_secure_driver():
    """
    Konfiguriert einen Chrome-Webdriver mit optimalen Einstellungen
    für zuverlässiges Laden von Inhalten.
    """
    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def wait_for_page_load(driver, timeout=30):
    """
    Wartet, bis die Seite vollständig geladen ist, mit mehreren Überprüfungen.
    """
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        WebDriverWait(driver, timeout / 2).until(
            lambda d: d.execute_script("return typeof jQuery === 'undefined' || jQuery.active === 0")
        )
        WebDriverWait(driver, timeout / 2).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)  # Zusätzliche Wartezeit für asynchrone Inhalte
        return True
    except TimeoutException:
        print("Warnung: Timeout beim Warten auf vollständiges Laden der Seite.")
        return False


def click_interactive_elements(driver, output_widget, max_attempts=3):
    """
    Klickt systematisch auf interaktive Elemente und wartet auf Inhaltsladung.
    """
    interactive_selectors = [
        "button:not([disabled])", "a.more", "a.show-more", "a.expand",
        ".toggle", ".accordion-header", ".accordion-button", "[aria-expanded='false']",
        "[data-toggle='collapse']", ".btn", ".load-more", "details:not([open]) > summary"
    ]

    try:
        viewport_height = driver.execute_script("return window.innerHeight")
        total_height = driver.execute_script("return document.body.scrollHeight")
        scroll_step = viewport_height // 3
        output_widget.insert(tk.END, "Scrolle durch die Seite für dynamische Inhalte...\n")
        for scroll_pos in range(0, total_height, scroll_step):
            driver.execute_script(f"window.scrollTo(0, {scroll_pos})")
            time.sleep(0.5)
        driver.execute_script("window.scrollTo(0, 0)")
    except Exception as e:
        output_widget.insert(tk.END, f"Fehler beim Scrollen: {str(e)}\n")

    clicked_elements = set()
    for selector in interactive_selectors:
        output_widget.insert(tk.END, f"Suche nach Elementen: {selector}\n")
        output_widget.update()
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                output_widget.insert(tk.END, f"{len(elements)} Elemente mit '{selector}' gefunden.\n")
                for elem in elements[:15]:
                    try:
                        if not elem.is_displayed():
                            continue
                        elem_id = f"{elem.text.strip()}_{elem.location['x']}_{elem.location['y']}"
                        if elem_id in clicked_elements:
                            continue
                        clicked_elements.add(elem_id)
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem)
                        time.sleep(1)
                        success = False
                        for _ in range(max_attempts):
                            try:
                                driver.execute_script("arguments[0].click();", elem)
                                success = True
                                break
                            except Exception:
                                time.sleep(0.5)
                        if success:
                            output_widget.insert(tk.END, "Element wurde erfolgreich geklickt.\n")
                            time.sleep(2)
                            wait_for_page_load(driver, timeout=5)
                        else:
                            output_widget.insert(tk.END, "Konnte Element nicht klicken.\n")
                    except StaleElementReferenceException:
                        output_widget.insert(tk.END, "Element nicht mehr verfügbar (StaleElementReference).\n")
                        continue
                    except Exception as e:
                        output_widget.insert(tk.END, f"Fehler: {str(e)}\n")
                        continue
        except Exception as e:
            output_widget.insert(tk.END, f"Fehler bei Selector {selector}: {str(e)}\n")

    driver.execute_script("window.scrollTo(0, 0)")
    time.sleep(1)


def detect_language(code_text):
    """Erkennt die Sprache eines Code-Blocks anhand typischer Muster."""
    language_patterns = [
        (r'function\s+\w+\s*\(|var\s+\w+\s*=|const\s+\w+\s*=|import\s+.*\s+from|export', 'javascript'),
        (r'def\s+\w+\s*\(|import\s+\w+|class\s+\w+:|if\s+.*:', 'python'),
        (r'<html|<body|<div|<script|<!DOCTYPE|<head', 'html'),
        (r'body\s*{|margin:|padding:|font-family:|@media', 'css'),
        (r'SELECT|INSERT INTO|UPDATE|DELETE FROM|CREATE TABLE', 'sql'),
        (r'version:|services:|image:|volumes:|environment:|restart:', 'yaml'),
        (r'#include|int\s+main|void\s+\w+\s*\(|printf|cout', 'cpp'),
        (r'public\s+class|private\s+void|protected|@Override', 'java')
    ]

    for pattern, lang in language_patterns:
        if re.search(pattern, code_text, re.IGNORECASE):
            return lang
    return ""


def identify_sections(text):
    """Identifiziert Abschnitte im Text, um ein Inhaltsverzeichnis zu generieren."""
    lines = text.split('\n')
    sections = []
    section_patterns = [
        r'^[0-9]+[\.\s]+[A-ZÄÖÜ][\w\s\-\–:]+$',
        r'^[A-ZÄÖÜ][\w\s\-\–]+:$',
        r'^[A-ZÄÖÜ]{2,}$'
    ]

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        for pattern in section_patterns:
            if re.match(pattern, line):
                sections.append((i, line))
                break
    return sections


def create_markdown_document(title, content, code_blocks, sections):
    """
    Erstellt ein formatiertes Markdown-Dokument inklusive Inhaltsverzeichnis und Code-Blöcken.
    Zusätzlich: Jede Zeile, die "click to open code" enthält, wird durch eine Codebox ersetzt.
    """
    markdown = "Hier findest du das vollständige Proof-of-Concept als Markdown-Dokument mit korrekt eingerücktem Code:\n\n"
    markdown += "---\n\n"
    markdown += f"# {title}\n\n"

    description_lines = []
    for line in content.split('\n')[:10]:
        line = line.strip()
        if line and len(line) > 20:
            description_lines.append(line)
            if len(description_lines) >= 3:
                break
    if description_lines:
        markdown += " ".join(description_lines) + "\n\n"
    markdown += "---\n\n"

    if len(sections) >= 3:
        markdown += "## Inhaltsverzeichnis\n\n"
        for idx, (_, sec_title) in enumerate(sections):
            clean_title = sec_title.rstrip(':')
            anchor = re.sub(r'[^a-z0-9\-]', '', clean_title.lower().replace(' ', '-'))
            markdown += f"{idx + 1}. [{clean_title}](#{anchor})\n"
        markdown += "\n---\n\n"

    processed_lines = []
    lines = content.split('\n')
    in_code = False
    code_start = None
    for i, line in enumerate(lines):
        # Falls die Zeile als Abschnitt erkannt wird, Überschrift hinzufügen
        if any(i == idx for idx, _ in sections):
            for idx, sec in sections:
                if i == idx:
                    processed_lines.append(f"## {sec.rstrip(':')}")
                    processed_lines.append("")
                    break
            continue

        # Falls die Zeile den Marker "click to open code" enthält, Platzhalter einfügen
        if "click to open code" in line.lower():
            processed_lines.append("<<<CODE_BLOCK_PLACEHOLDER>>>")
            continue

        # Optional: Erkennung von Code-Blöcken im Fließtext (z.B. bei "def", "import", "class")
        if not in_code and (line.strip().startswith("def ") or
                            line.strip().startswith("import ") or
                            line.strip().startswith("class ")):
            in_code = True
            code_start = i
            continue
        elif in_code:
            if not line.strip():
                in_code = False
                code_text = "\n".join(lines[code_start:i])
                language = detect_language(code_text)
                processed_lines.append(f"```{language}")
                processed_lines.append(code_text)
                processed_lines.append("```")
                processed_lines.append("")
                continue
        processed_lines.append(line)

    # Ersetze Platzhalter durch die extrahierten Code-Blöcke
    final_lines = []
    code_idx = 0
    for line in processed_lines:
        if line.strip() == "<<<CODE_BLOCK_PLACEHOLDER>>>":
            if code_idx < len(code_blocks):
                code_text = code_blocks[code_idx]["text"]
                language = code_blocks[code_idx]["language"]
                final_lines.append(f"```{language}")
                final_lines.append(code_text)
                final_lines.append("```")
                final_lines.append("")
                code_idx += 1
            else:
                final_lines.append("`Kein Code gefunden`")
        else:
            final_lines.append(line)

    markdown += "\n".join(final_lines)

    # Hänge alle noch nicht eingebetteten Code-Blöcke ans Ende an
    for idx in range(code_idx, len(code_blocks)):
        code_text = code_blocks[idx]["text"]
        language = code_blocks[idx]["language"]
        markdown += f"\n\n```{language}\n{code_text}\n```"

    markdown += "\n\n---"
    markdown = re.sub(r'\n{4,}', '\n\n\n', markdown)
    return markdown


def extract_content_with_code_blocks(driver, output_widget):
    """
    Extrahiert Titel, Hauptinhalt und alle Code-Blöcke von der Seite.
    """
    try:
        title = driver.title or "Extrahierter Inhalt"
        output_widget.insert(tk.END, f"Seitentitel: {title}\n")
    except Exception:
        title = "Extrahierter Inhalt"
        output_widget.insert(tk.END, "Konnte den Seitentitel nicht ermitteln.\n")

    main_content = ""
    selectors = ["main", "#main", ".main-content", "article", ".content", "#content"]
    for selector in selectors:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, selector)
            if elems:
                for elem in elems:
                    main_content += elem.text + "\n\n"
                output_widget.insert(tk.END, f"Hauptinhalt mit Selector '{selector}' gefunden.\n")
                break
        except Exception:
            continue
    if not main_content.strip():
        try:
            main_content = driver.find_element(By.TAG_NAME, "body").text
            output_widget.insert(tk.END, "Kein spezifischer Hauptinhalt gefunden – Body-Text verwendet.\n")
        except Exception:
            raise Exception("Kein Textinhalt gefunden.")

    code_blocks = []
    code_selectors = ["pre", "code", ".code", ".hljs", ".syntax-highlighting", "[class*='language-']"]
    output_widget.insert(tk.END, "Suche nach Code-Blöcken...\n")
    for selector in code_selectors:
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, selector)
            for elem in elems:
                text = elem.text.strip()
                if text:
                    language = detect_language(text)
                    code_blocks.append({"text": text, "language": language})
        except Exception as e:
            output_widget.insert(tk.END, f"Fehler bei Code-Selector {selector}: {str(e)}\n")
    output_widget.insert(tk.END, f"Insgesamt {len(code_blocks)} Code-Blöcke extrahiert.\n")
    return title, main_content, code_blocks


def process_page(url, output_widget):
    """
    Hauptfunktion: Lädt die Seite, interagiert, extrahiert Inhalte und speichert das Markdown.
    """
    driver = None
    try:
        output_widget.delete(1.0, tk.END)
        output_widget.insert(tk.END, f"Starte Browser und lade Seite: {url}\n")
        driver = get_secure_driver()
        driver.get(url)
        output_widget.insert(tk.END, "Warte auf vollständiges Laden der Seite...\n")
        if wait_for_page_load(driver):
            output_widget.insert(tk.END, "Seite wurde erfolgreich geladen.\n")
        else:
            output_widget.insert(tk.END, "Seite wurde geladen, aber möglicherweise nicht vollständig.\n")

        if not messagebox.askokcancel("Manuelle Eingabe",
                                      "Bitte schließe störende Popups und führe notwendige Aktionen durch. Klicke OK, wenn alles bereit ist."):
            output_widget.insert(tk.END, "Prozess wurde vom Nutzer abgebrochen.\n")
            return

        output_widget.insert(tk.END, "Starte automatisches Klicken auf interaktive Elemente...\n")
        click_interactive_elements(driver, output_widget)

        output_widget.insert(tk.END, "Extrahiere Inhalte und Code-Blöcke...\n")
        title, content, code_blocks = extract_content_with_code_blocks(driver, output_widget)

        sections = identify_sections(content)
        output_widget.insert(tk.END, f"{len(sections)} Abschnitte identifiziert.\n")

        markdown_text = create_markdown_document(title, content, code_blocks, sections)

        # Datei speichern
        save_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown Dateien", "*.md"), ("Alle Dateien", "*.*")],
            title="Speicherort für Markdown-Dokument wählen"
        )
        if not save_path:
            output_widget.insert(tk.END, "Speicheraktion abgebrochen.\n")
            return

        with open(save_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        output_widget.insert(tk.END, "\n--- Vorschau des generierten Markdown-Dokuments ---\n\n")
        preview = markdown_text if len(markdown_text) < 2000 else markdown_text[:2000] + "\n...(gekürzt)"
        output_widget.insert(tk.END, preview)

        output_widget.insert(tk.END, "\n\nFeedback: Markdown-Dokument wurde erfolgreich erstellt und in die Datei gespeichert!\n")
        messagebox.showinfo("Erfolg", f"Das Markdown-Dokument wurde erfolgreich unter {save_path} gespeichert!")
    except Exception as e:
        err_msg = f"Fehler bei der Verarbeitung: {str(e)}"
        output_widget.insert(tk.END, f"\nFEHLER: {err_msg}\n")
        messagebox.showerror("Fehler", err_msg)
    finally:
        if driver:
            try:
                driver.quit()
                output_widget.insert(tk.END, "\nBrowser wurde geschlossen.\n")
            except Exception:
                pass


def start_processing(url_entry, output_widget):
    """Startet den Verarbeitungsprozess in einem separaten Thread."""
    url = url_entry.get().strip()
    if not url:
        messagebox.showwarning("Warnung", "Bitte eine URL eingeben.")
        return
    thread = threading.Thread(target=process_page, args=(url, output_widget))
    thread.daemon = True
    thread.start()


def create_ui():
    """Erstellt die Benutzeroberfläche mit einer URL-Eingabe, Statusanzeige und Feedback."""
    root = tk.Tk()
    root.title("Markdown-Extraktor für DevOps-Infrastruktur")
    root.geometry("1000x800")

    mainframe = ttk.Frame(root, padding="10")
    mainframe.pack(fill=tk.BOTH, expand=True)

    url_frame = ttk.Frame(mainframe)
    url_frame.pack(fill=tk.X, pady=5)
    ttk.Label(url_frame, text="URL:").pack(side=tk.LEFT, padx=5)
    url_entry = ttk.Entry(url_frame, width=60)
    url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    url_entry.insert(0, "https://example.com")

    start_button = ttk.Button(
        url_frame,
        text="Seite laden und verarbeiten",
        command=lambda: start_processing(url_entry, output_text)
    )
    start_button.pack(side=tk.LEFT, padx=5)

    output_frame = ttk.LabelFrame(mainframe, text="Status und Vorschau")
    output_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD)
    output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    output_text.insert(tk.END,
                       "=== Markdown-Extraktor gestartet ===\n\nBitte gib die URL der Seite ein und klicke auf 'Seite laden und verarbeiten'.\n")

    def on_close():
        if messagebox.askokcancel("Beenden", "Möchtest du das Programm wirklich beenden?"):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    create_ui()
