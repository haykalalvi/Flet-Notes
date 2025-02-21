import flet as ft
import os
import sounddevice as sd
import wave
import numpy as np

NOTES_DIR = "notes"
AUDIO_DIR = "voice_notes"

import mysql.connector

# Koneksi ke database
db = mysql.connector.connect(
    host="Alvis-MacBook-Pro.local",
    user="root",  # Sesuaikan dengan user MySQL-mu
    password="Maubelajar14",  # Isi dengan password MySQL-mu
    database="notes_db"
)
cursor = db.cursor()


for directory in [NOTES_DIR, AUDIO_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_note_list():
    """Mengambil daftar semua catatan dari database."""
    cursor.execute("SELECT name FROM notes")
    return [row[0] for row in cursor.fetchall()]

def load_note(note_name):
    """Memuat isi catatan tertentu dari database."""
    cursor.execute("SELECT content FROM notes WHERE name = %s", (note_name,))
    result = cursor.fetchone()
    return result[0] if result else ""

def save_note(note_name, text):
    """Menyimpan atau memperbarui catatan ke database."""
    cursor.execute("INSERT INTO notes (name, content) VALUES (%s, %s) ON DUPLICATE KEY UPDATE content = %s",
                   (note_name, text, text))
    db.commit()

def delete_note(note_name, page, note_dropdown, text_field):
    """Menghapus catatan yang dipilih dari database."""
    cursor.execute("DELETE FROM notes WHERE name = %s", (note_name,))
    db.commit()

    note_dropdown.options = [ft.dropdown.Option(name) for name in get_note_list()]
    note_dropdown.value = None
    text_field.value = ""
    page.update()

def rename_note(old_name, new_name, page, note_dropdown, text_field):
    """Mengubah nama catatan dalam database."""
    cursor.execute("UPDATE notes SET name = %s WHERE name = %s", (new_name, old_name))
    db.commit()

    note_dropdown.options = [ft.dropdown.Option(name) for name in get_note_list()]
    note_dropdown.value = new_name
    text_field.value = load_note(new_name)
    page.update()


def search_notes(query, note_dropdown, page):
    note_dropdown.options = [
        ft.dropdown.Option(name) for name in get_note_list() if query.lower() in name.lower()
    ]
    page.update()

def record_audio(note_name, duration=5, samplerate=44100):
    audio_path = os.path.join(AUDIO_DIR, f"{note_name}.wav")
    print(f"Merekam audio selama {duration} detik...")
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype=np.int16)
    sd.wait()
    with wave.open(audio_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(recording.tobytes())
    print("Rekaman selesai!")

def play_audio(note_name):
    audio_path = os.path.join(AUDIO_DIR, f"{note_name}.wav")
    if os.path.exists(audio_path):
        with wave.open(audio_path, "rb") as wf:
            samplerate = wf.getframerate()
            data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
            sd.play(data, samplerate)
            sd.wait()

def main(page: ft.Page):
    page.title = "Multi-Notes dengan Voice Notes"
    page.scroll = True
    page.theme_mode = ft.ThemeMode.LIGHT
    note_list = get_note_list()

    note_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(name) for name in note_list],
        width=250,
        on_change=lambda e: load_selected_note(e, text_field),
    )

    text_field = ft.TextField(
        multiline=True,
        expand=True,
        autofocus=True,
        border=ft.InputBorder.NONE,
        min_lines=30,
        content_padding=30,
        cursor_color="black",
        value="",
        on_change=lambda e: save_note(note_dropdown.value, text_field.value) if note_dropdown.value else None,
    )

    def load_selected_note(e, text_field):
        selected_note = note_dropdown.value
        if selected_note:
            text_field.value = load_note(selected_note)
            page.update()

    def create_new_note(e):
        new_note_name = new_note_field.value.strip()
        if new_note_name and new_note_name not in get_note_list():
            save_note(new_note_name, "")  # Simpan catatan baru
            note_dropdown.options.append(ft.dropdown.Option(new_note_name))
            note_dropdown.value = new_note_name
            text_field.value = ""
            page.update()


    def delete_selected_note(e):
        if note_dropdown.value:
            show_delete_confirmation(note_dropdown.value)

    def show_delete_confirmation(note_name):
        """Menampilkan dialog konfirmasi sebelum menghapus catatan"""
        def confirm_delete(e):
            delete_note(note_name, page, note_dropdown, text_field)
            page.close(dialog)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Konfirmasi Hapus"),
            content=ft.Text(f"Apakah Anda yakin ingin menghapus catatan '{note_name}'?"),
            actions=[
                ft.TextButton("Ya", on_click=confirm_delete),
                ft.TextButton("Tidak", on_click=lambda e: page.close(dialog))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.open(dialog)
        
    def rename_selected_note(e):
        new_name = rename_field.value.strip()
        if note_dropdown.value and new_name:
            rename_note(note_dropdown.value, new_name, page, note_dropdown, text_field)

    def search_handler(e):
        search_notes(search_field.value, note_dropdown, page)

    def record_voice_note(e):
        if note_dropdown.value:
            record_audio(note_dropdown.value)
            page.update()

    def play_voice_note(e):
        if note_dropdown.value:
            play_audio(note_dropdown.value)

    search_field = ft.TextField(hint_text="Cari catatan...", width=200, on_change=search_handler)
    record_button = ft.ElevatedButton("Rekam", on_click=record_voice_note)
    play_button = ft.ElevatedButton("Putar", on_click=play_voice_note)

    new_note_field = ft.TextField(hint_text="Nama catatan baru...", width=200, on_submit=create_new_note)
    add_note_button = ft.ElevatedButton("Buat Catatan", on_click=create_new_note)

    rename_field = ft.TextField(hint_text="Nama baru...", width=200, on_submit=rename_selected_note)
    rename_button = ft.ElevatedButton("Ubah Nama", on_click=rename_selected_note)

    delete_button = ft.ElevatedButton("Hapus Catatan", on_click=delete_selected_note, bgcolor="red")

    page.add(
        ft.Row(
            [search_field, ft.Container(expand=True), record_button, play_button],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        ft.Row([note_dropdown, new_note_field, add_note_button], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([rename_field, rename_button, delete_button], alignment=ft.MainAxisAlignment.CENTER),
        text_field,
    )

ft.app(target=main)
