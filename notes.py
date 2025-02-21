import flet as ft
import os

NOTES_FILE = "notes.txt"

def load_notes():
    """Memuat catatan dari file jika tersedia."""
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r", encoding="utf-8") as file:
            return file.read()
    return ""

def save_notes(content):
    """Menyimpan catatan ke dalam file."""
    with open(NOTES_FILE, "w", encoding="utf-8") as file:
        file.write(content)

def main(page: ft.Page):
    page.title = "Simple Notes"
    page.scroll = True

    text_field = ft.TextField(
        multiline=True,
        expand=True,
        value=load_notes(),
        hint_text="Tulis catatan Anda di sini..."
    )

    def on_close(e):
        """Event saat aplikasi ditutup, menyimpan catatan."""
        save_notes(text_field.value)

    page.on_close = on_close
    page.add(text_field)

ft.app(target=main)
