import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path


class LibraryApp:
    """Приложение для учёта прочитанных книг."""

    DB_FILENAME = "books.json"

    def __init__(self, window):
        self.window = window
        self.window.title("Book Tracker — Трекер прочитанных книг")
        self.window.geometry("920x620")
        self.window.resizable(True, True)

        self.collection = []
        self._build_ui()
        self._load_from_disk()

    # ======================== GUI ========================

    def _build_ui(self):
        # Верхний блок: форма ввода
        form_block = ttk.LabelFrame(self.window, text="Данные книги", padding=12)
        form_block.pack(fill="x", padx=12, pady=(12, 4))

        self._make_entry(form_block, "Название:", 0, "title_input")
        self._make_entry(form_block, "Автор:",    1, "author_input")
        self._make_entry(form_block, "Жанр:",     2, "genre_input")
        self._make_entry(form_block, "Страниц:",  3, "pages_input")

        ttk.Button(form_block, text="Добавить в список", command=self._add_to_collection)\
            .grid(row=4, column=0, columnspan=2, pady=(10, 0))

        # Средний блок: фильтры
        filter_block = ttk.LabelFrame(self.window, text="Фильтры", padding=12)
        filter_block.pack(fill="x", padx=12, pady=4)

        ttk.Label(filter_block, text="Жанр:").grid(row=0, column=0, sticky="w")
        self.genre_dropdown = ttk.Combobox(filter_block, width=30, state="readonly")
        self.genre_dropdown.grid(row=0, column=1, padx=6)
        self.genre_dropdown.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        ttk.Label(filter_block, text="Минимум страниц:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.pages_threshold = ttk.Entry(filter_block, width=32)
        self.pages_threshold.grid(row=1, column=1, padx=6, pady=(8, 0))
        self.pages_threshold.bind("<KeyRelease>", lambda e: self._apply_filters())

        ttk.Button(filter_block, text="Сбросить", command=self._reset_filters)\
            .grid(row=2, column=0, columnspan=2, pady=(10, 0))

        # Таблица
        table_frame = ttk.Frame(self.window)
        table_frame.pack(fill="both", expand=True, padx=12, pady=4)

        columns = ("Название", "Автор", "Жанр", "Страниц")
        self.table = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, width=210)

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroll_y.set)
        self.table.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        # Нижние кнопки
        action_bar = ttk.Frame(self.window)
        action_bar.pack(fill="x", padx=12, pady=(4, 12))

        ttk.Button(action_bar, text="Сохранить (JSON)", command=self._save_to_disk).pack(side="left", padx=4)
        ttk.Button(action_bar, text="Загрузить (JSON)", command=self._load_from_disk).pack(side="left", padx=4)
        ttk.Button(action_bar, text="Удалить книгу", command=self._delete_selected).pack(side="left", padx=4)

        self.statusbar = ttk.Label(self.window, text="Готово", relief="sunken", anchor="w")
        self.statusbar.pack(fill="x", padx=12, pady=(0, 8))

    def _make_entry(self, parent, label_text, row, attr_name):
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w", pady=3)
        entry = ttk.Entry(parent, width=42)
        entry.grid(row=row, column=1, padx=6, pady=3)
        setattr(self, attr_name, entry)

    # ====================== ЛОГИКА ======================

    def _validate_form(self):
        raw_title = self.title_input.get().strip()
        raw_author = self.author_input.get().strip()
        raw_genre = self.genre_input.get().strip()
        raw_pages = self.pages_input.get().strip()

        if not all([raw_title, raw_author, raw_genre, raw_pages]):
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return None

        if not raw_pages.isdigit():
            messagebox.showerror("Ошибка", "Количество страниц — целое число!")
            return None

        pages_num = int(raw_pages)
        if pages_num <= 0:
            messagebox.showerror("Ошибка", "Число страниц должно быть положительным!")
            return None

        return {
            "title": raw_title,
            "author": raw_author,
            "genre": raw_genre,
            "pages": pages_num,
        }

    def _add_to_collection(self):
        record = self._validate_form()
        if record is None:
            return
        self.collection.append(record)
        self._refresh_table()
        self._wipe_inputs()
        self._update_genre_options()
        self.statusbar.config(text=f"Добавлена книга: «{record['title']}»")

    def _wipe_inputs(self):
        for attr in ("title_input", "author_input", "genre_input", "pages_input"):
            getattr(self, attr).delete(0, tk.END)

    def _refresh_table(self, subset=None):
        for row_id in self.table.get_children():
            self.table.delete(row_id)
        source = subset if subset is not None else self.collection
        for item in source:
            self.table.insert("", tk.END,
                              values=(item["title"], item["author"],
                                      item["genre"], item["pages"]))

    def _apply_filters(self):
        filtered = list(self.collection)

        chosen_genre = self.genre_dropdown.get()
        if chosen_genre and chosen_genre != "(все)":
            filtered = [b for b in filtered if b["genre"] == chosen_genre]

        threshold_str = self.pages_threshold.get().strip()
        if threshold_str:
            if threshold_str.isdigit():
                limit = int(threshold_str)
                filtered = [b for b in filtered if b["pages"] > limit]
            else:
                self.statusbar.config(text="⚠ В фильтре страниц введите число!")
                return

        self._refresh_table(filtered)
        self.statusbar.config(text=f"Показано книг: {len(filtered)}")

    def _reset_filters(self):
        self.genre_dropdown.set("")
        self.pages_threshold.delete(0, tk.END)
        self._refresh_table()
        self.statusbar.config(text="Фильтры сброшены")

    def _update_genre_options(self):
        genres = sorted({b["genre"] for b in self.collection})
        genres.insert(0, "(все)")
        self.genre_dropdown["values"] = genres

    def _delete_selected(self):
        selection = self.table.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Сначала выберите книгу в таблице.")
            return
        values = self.table.item(selection[0])["values"]
        self.collection = [b for b in self.collection
                           if not (b["title"] == values[0] and
                                   b["author"] == values[1] and
                                   b["genre"] == values[2] and
                                   b["pages"] == int(values[3]))]
        self._refresh_table()
        self._update_genre_options()
        self.statusbar.config(text="Книга удалена")

    # ====================== JSON ========================

    def _save_to_disk(self):
        try:
            with open(self.DB_FILENAME, "w", encoding="utf-8") as fh:
                json.dump(self.collection, fh, ensure_ascii=False, indent=2)
            messagebox.showinfo("OK", f"Данные записаны в {self.DB_FILENAME}")
        except OSError as err:
            messagebox.showerror("Ошибка", f"Не могу сохранить: {err}")

    def _load_from_disk(self):
        path = Path(self.DB_FILENAME)
        if not path.exists():
            self.collection = []
            return
        try:
            self.collection = json.loads(path.read_text(encoding="utf-8"))
            self._refresh_table()
            self._update_genre_options()
            self.statusbar.config(text=f"Загружено книг: {len(self.collection)}")
        except (json.JSONDecodeError, OSError) as err:
            messagebox.showerror("Ошибка", f"Не могу загрузить: {err}")
            self.collection = []


if __name__ == "__main__":
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()