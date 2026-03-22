import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

# ====================== АЛФАВИТЫ ======================
PLAYFAIR_ALPHABET = "ABCDEFGHIKLMNOPQRSTUVWXYZ"
RUSSIAN_ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"


# ====================== PLAYFAIR ======================
def build_playfair_table(key: str):
    full_key = ""
    seen = set()
    for c in key.upper():
        c = "I" if c == "J" else c
        if c in PLAYFAIR_ALPHABET and c not in seen:
            full_key += c
            seen.add(c)
    for c in PLAYFAIR_ALPHABET:
        if c not in seen:
            full_key += c
    return [list(full_key[i*5:(i+1)*5]) for i in range(5)]


def find_position(c: str, table):
    for r in range(5):
        for col in range(5):
            if table[r][col] == c:
                return r, col
    return None


def encrypt_playfair_pair(a: str, b: str, table):
    r1, c1 = find_position(a, table)
    r2, c2 = find_position(b, table)
    if r1 == r2:
        return table[r1][(c1 + 1) % 5], table[r2][(c2 + 1) % 5]
    elif c1 == c2:
        return table[(r1 + 1) % 5][c1], table[(r2 + 1) % 5][c2]
    else:
        return table[r1][c2], table[r2][c1]


def decrypt_playfair_pair(a: str, b: str, table):
    r1, c1 = find_position(a, table)
    r2, c2 = find_position(b, table)
    if r1 == r2:
        return table[r1][(c1 + 4) % 5], table[r2][(c2 + 4) % 5]
    elif c1 == c2:
        return table[(r1 + 4) % 5][c1], table[(r2 + 4) % 5][c2]
    else:
        return table[r1][c2], table[r2][c1]


class PlayfairProcessor:
    def __init__(self, table, encrypt: bool):
        self.table = table
        self.encrypt = encrypt
        self.pending = None

    def process(self, c: str) -> str:
        c = c.upper()
        if c == "J":
            c = "I"
        if c in PLAYFAIR_ALPHABET:
            if self.pending is None:
                self.pending = c
                return ""
            else:
                a, b = self.pending, c
                p1, p2 = (encrypt_playfair_pair if self.encrypt else decrypt_playfair_pair)(a, b, self.table)
                self.pending = None
                return p1 + p2
        return c

    def flush(self) -> str:
        if self.pending:
            p1, p2 = (encrypt_playfair_pair if self.encrypt else decrypt_playfair_pair)(self.pending, "X", self.table)
            self.pending = None
            return p1 + p2
        return ""


# ====================== VIGENERE (прогрессивный ключ) ======================
def prepare_vigenere_key(key: str) -> str:
    return "".join(c.upper() for c in key if c.upper() in RUSSIAN_ALPHABET)


class VigenereProcessor:
    def __init__(self, key: str, encrypt: bool):
        # key – очищенная строка (только русские буквы)
        self.base_key = key
        self.base_indices = [RUSSIAN_ALPHABET.index(ch) for ch in key]  # индексы базового ключа
        self.encrypt = encrypt
        self.index = 0          # позиция обработанной русской буквы

    def process(self, c: str) -> str:
        c_upper = c.upper()
        if c_upper in RUSSIAN_ALPHABET:
            idx = RUSSIAN_ALPHABET.index(c_upper)
            # Вычисляем прогрессивный ключ:
            # номер блока = self.index // len(self.base_key)
            # позиция внутри блока = self.index % len(self.base_key)
            block = self.index // len(self.base_key)
            pos = self.index % len(self.base_key)
            # фактический индекс ключа = (базовый_индекс[pos] + block) % 33
            key_char_idx = (self.base_indices[pos] + block) % 33
            if self.encrypt:
                new_idx = (idx + key_char_idx) % 33
            else:
                new_idx = (idx - key_char_idx + 33) % 33
            result = RUSSIAN_ALPHABET[new_idx]
            self.index += 1
            return result
        return c

    def flush(self) -> str:
        return ""


# ====================== ГЛАВНОЕ ОКНО ======================
class CryptoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Шифрование текста")
        self.geometry("800x350")
        self.minsize(700, 300)
        self.configure(bg="#f0f0f0")

        self.algo_var = tk.StringVar(value="playfair")

        style = ttk.Style(self)
        style.theme_use("clam")

        self.create_menu()
        self.create_widgets()

    def create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Открыть...", command=self.open_file)
        file_menu.add_command(label="Сохранить результат...", command=self.save_result)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.quit)

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, content)
            self.status.config(text=f"Загружен: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать файл:\n{str(e)}")

    def save_result(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Текстовые файлы", "*.txt")])
        if not path:
            return
        try:
            content = self.output_entry.get()
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self.status.config(text=f"Результат сохранён: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")

    def create_widgets(self):
        # --- Верхний фрейм: выбор алгоритма и ключ ---
        frame_top = ttk.LabelFrame(self, text="Алгоритм и ключ")
        frame_top.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_top, text="Выберите алгоритм:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Radiobutton(frame_top, text="Плейфейр (английский)", variable=self.algo_var, value="playfair").grid(row=1, column=0, sticky="w", padx=20)
        ttk.Radiobutton(frame_top, text="Виженер (русский, прогрессивный ключ)", variable=self.algo_var, value="vigenere").grid(row=2, column=0, sticky="w", padx=20)

        ttk.Label(frame_top, text="Ключ:").grid(row=0, column=1, sticky="e", padx=5, pady=5)
        self.key_entry = ttk.Entry(frame_top, width=40, font=("Segoe UI", 11))
        self.key_entry.grid(row=1, column=1, rowspan=2, sticky="ew", padx=10)

        frame_top.columnconfigure(1, weight=1)

        # --- Фрейм для исходного текста и результата (однострочные поля) ---
        frame_io = ttk.Frame(self)
        frame_io.pack(fill="x", padx=10, pady=5)

        # Исходный текст
        ttk.Label(frame_io, text="Исходный текст:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.input_entry = ttk.Entry(frame_io, width=60, font=("Consolas", 11))
        self.input_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Результат
        ttk.Label(frame_io, text="Результат:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.output_entry = ttk.Entry(frame_io, width=60, font=("Consolas", 11), state="readonly")
        self.output_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        frame_io.columnconfigure(1, weight=1)

        # --- Фрейм с кнопками ---
        frame_buttons = ttk.Frame(self)
        frame_buttons.pack(pady=10)

        ttk.Button(frame_buttons, text="Зашифровать", command=lambda: self.process_text(True)).pack(side="left", padx=5)
        ttk.Button(frame_buttons, text="Расшифровать", command=lambda: self.process_text(False)).pack(side="left", padx=5)
        ttk.Button(frame_buttons, text="Показать процесс", command=self.show_visualization).pack(side="left", padx=5)

        # Статусная строка
        self.status = ttk.Label(self, text="Готов к работе", relief="sunken", anchor="center")
        self.status.pack(fill="x", side="bottom", padx=10, pady=5)

    # ====================== ДОПОЛНИТЕЛЬНАЯ ФИЛЬТРАЦИЯ ======================
    def filter_text_for_algo(self, text: str, algo: str) -> tuple[str, int]:
        if algo == "playfair":
            filtered = []
            for ch in text.upper():
                if ch == 'J':
                    filtered.append('I')
                elif ch in PLAYFAIR_ALPHABET:
                    filtered.append(ch)
            filtered_text = ''.join(filtered)
            removed = len(text) - len(filtered_text)
            return filtered_text, removed
        else:
            filtered = [ch for ch in text if ch.upper() in RUSSIAN_ALPHABET]
            filtered_text = ''.join(filtered)
            removed = len(text) - len(filtered_text)
            return filtered_text, removed

    # ====================== ОБРАБОТКА ======================
    def get_processor(self, encrypt: bool):
        raw_key = self.key_entry.get().strip()
        algo = self.algo_var.get()

        if not raw_key:
            messagebox.showwarning("Внимание", "Введите ключ")
            return None

        if len(raw_key) > 100:
            messagebox.showwarning("Внимание", "Ключ не должен превышать 100 символов")
            return None

        if algo == "playfair":
            has_english = any(c.upper() in PLAYFAIR_ALPHABET for c in raw_key)
            if not has_english:
                messagebox.showwarning("Внимание", "Ключ для Плейфейра должен содержать английские буквы (A-Z)")
                return None
            table = build_playfair_table(raw_key)
            return PlayfairProcessor(table, encrypt)
        else:
            clean_key = prepare_vigenere_key(raw_key)
            if not clean_key:
                messagebox.showwarning("Внимание", "Ключ для Виженера должен содержать русские буквы (включая Ё)")
                return None
            if len(clean_key) > 100:
                messagebox.showwarning("Внимание", "Ключ (после удаления не-букв) не должен превышать 100 символов")
                return None
            return VigenereProcessor(clean_key, encrypt)

    def process_text(self, encrypt: bool):
        text = self.input_entry.get()
        if not text:
            messagebox.showwarning("Внимание", "Введите текст")
            return

        algo = self.algo_var.get()
        filtered_text, removed = self.filter_text_for_algo(text, algo)

        if not filtered_text:
            messagebox.showwarning("Внимание", f"Текст не содержит подходящих букв для алгоритма "
                                                f"{'Плейфейр (английские буквы)' if algo == 'playfair' else 'Виженер (русские буквы)'}.\n"
                                                f"Все символы были удалены.")
            return

        if removed > 0:
            msg = f"Удалено {removed} символов, не подходящих для алгоритма. " \
                  f"Будут обработаны только подходящие буквы."
            messagebox.showinfo("Фильтрация текста", msg)

        proc = self.get_processor(encrypt)
        if not proc:
            return

        result = "".join(proc.process(c) for c in filtered_text) + proc.flush()

        self.output_entry.configure(state="normal")
        self.output_entry.delete(0, tk.END)
        self.output_entry.insert(0, result)
        self.output_entry.configure(state="readonly")

        self.status.config(text="Текст обработан ✓")

    # ====================== ВИЗУАЛИЗАЦИЯ ======================
    def show_visualization(self):
        text = self.input_entry.get()
        if not text:
            messagebox.showwarning("Внимание", "Сначала введите текст!")
            return

        key = self.key_entry.get().strip()
        if not key:
            messagebox.showwarning("Внимание", "Введите ключ!")
            return

        algo = self.algo_var.get()
        if len(key) > 100:
            messagebox.showwarning("Внимание", "Ключ не должен превышать 100 символов")
            return

        if algo == "playfair":
            has_english = any(c.upper() in PLAYFAIR_ALPHABET for c in key)
            if not has_english:
                messagebox.showwarning("Внимание", "Ключ для Плейфейра должен содержать английские буквы (A-Z)")
                return
        else:
            clean_key = prepare_vigenere_key(key)
            if not clean_key:
                messagebox.showwarning("Внимание", "Ключ для Виженера должен содержать русские буквы (включая Ё)")
                return
            if len(clean_key) > 100:
                messagebox.showwarning("Внимание", "Ключ (после удаления не-букв) не должен превышать 100 символов")
                return

        vis = tk.Toplevel(self)
        vis.title("Визуализация процесса шифрования")
        vis.geometry("1200x800")
        vis.configure(bg="#f8f9fa")

        ttk.Label(vis, text=f"Алгоритм: {'Плейфейр' if algo == 'playfair' else 'Виженер (прогрессивный ключ)'}",
                  font=("Segoe UI", 14, "bold")).pack(pady=10)

        if algo == "playfair":
            self.show_playfair_visual(vis, text, key)
        else:
            self.show_vigenere_visual(vis, text, key)

    def show_playfair_visual(self, window, text, key):
        table = build_playfair_table(key)

        frame_table = ttk.LabelFrame(window, text="Таблица Плейфейра 5×5")
        frame_table.pack(pady=10, padx=20, fill="x")
        for r in range(5):
            for c in range(5):
                lbl = ttk.Label(frame_table, text=table[r][c], font=("Consolas", 16, "bold"),
                                width=3, relief="solid", anchor="center")
                lbl.grid(row=r, column=c, padx=2, pady=2)

        clean = []
        for ch in text.upper():
            if ch == 'J':
                clean.append('I')
            elif ch in PLAYFAIR_ALPHABET:
                clean.append(ch)
        clean_text = ''.join(clean)

        if len(clean_text) == 0:
            ttk.Label(window, text="Нет букв для обработки").pack()
            return

        pairs = []
        i = 0
        while i < len(clean_text):
            a = clean_text[i]
            if i + 1 < len(clean_text):
                b = clean_text[i + 1]
                i += 2
            else:
                b = 'X'
                i += 1
            pairs.append((a, b))

        frame_pairs = ttk.LabelFrame(window, text="Пошаговый разбор (все пары)")
        frame_pairs.pack(pady=15, padx=20, fill="both", expand=True)

        columns = ("№", "Пара", "Позиции", "Правило", "Результат")
        tree = ttk.Treeview(frame_pairs, columns=columns, show="headings", height=20)
        tree.heading("№", text="№")
        tree.heading("Пара", text="Пара")
        tree.heading("Позиции", text="Позиции (строка,столбец)")
        tree.heading("Правило", text="Правило")
        tree.heading("Результат", text="Результат")

        tree.column("№", width=40, anchor="center")
        tree.column("Пара", width=80, anchor="center")
        tree.column("Позиции", width=200, anchor="center")
        tree.column("Правило", width=220, anchor="w")
        tree.column("Результат", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(frame_pairs, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for idx, (a, b) in enumerate(pairs, start=1):
            r1, c1 = find_position(a, table)
            r2, c2 = find_position(b, table)

            if r1 == r2:
                rule = "одна строка → сдвиг вправо"
            elif c1 == c2:
                rule = "один столбец → сдвиг вниз"
            else:
                rule = "прямоугольник → обмен углами"

            enc1, enc2 = encrypt_playfair_pair(a, b, table)
            pos_text = f"{a}({r1},{c1}) и {b}({r2},{c2})"
            tree.insert("", "end", values=(idx, f"{a}{b}", pos_text, rule, f"{enc1}{enc2}"))

        ttk.Label(window, text="* Если длина текста нечётная, последний символ дополнен 'X'.",
                  font=("Segoe UI", 10)).pack(pady=5)

    def show_vigenere_visual(self, window, text, key):
        clean_key = prepare_vigenere_key(key)
        if not clean_key:
            ttk.Label(window, text="Ключ не содержит русских букв").pack()
            return

        # Подготовка индексов базового ключа
        base_indices = [RUSSIAN_ALPHABET.index(ch) for ch in clean_key]
        L = len(clean_key)

        # Фрейм с пошаговой таблицей
        frame_steps = ttk.LabelFrame(window, text="Пошаговая таблица шифрования (все символы)")
        frame_steps.pack(pady=10, padx=20, fill="both", expand=True)

        columns = ("#", "Символ", "Тип", "Буква ключа (базовая)", "Блок", "Позиция", "Факт. ключ", "i_буквы", "Результат")
        tree_steps = ttk.Treeview(frame_steps, columns=columns, show="headings", height=15)
        tree_steps.heading("#", text="№")
        tree_steps.heading("Символ", text="Символ")
        tree_steps.heading("Тип", text="Тип")
        tree_steps.heading("Буква ключа (базовая)", text="Буква ключа (базовая)")
        tree_steps.heading("Блок", text="Блок")
        tree_steps.heading("Позиция", text="Позиция")
        tree_steps.heading("Факт. ключ", text="Факт. ключ")
        tree_steps.heading("i_буквы", text="i_буквы")
        tree_steps.heading("Результат", text="Результат")

        tree_steps.column("#", width=40, anchor="center")
        tree_steps.column("Символ", width=70, anchor="center")
        tree_steps.column("Тип", width=60, anchor="center")
        tree_steps.column("Буква ключа (базовая)", width=120, anchor="center")
        tree_steps.column("Блок", width=50, anchor="center")
        tree_steps.column("Позиция", width=60, anchor="center")
        tree_steps.column("Факт. ключ", width=80, anchor="center")
        tree_steps.column("i_буквы", width=70, anchor="center")
        tree_steps.column("Результат", width=100, anchor="center")

        scrollbar_y = ttk.Scrollbar(frame_steps, orient="vertical", command=tree_steps.yview)
        tree_steps.configure(yscrollcommand=scrollbar_y.set)
        tree_steps.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")

        # Прогрессивный ключ
        prog_key_letters = []
        idx = 0  # номер обработанной русской буквы
        for pos, ch in enumerate(text, start=1):
            ch_upper = ch.upper()
            if ch_upper in RUSSIAN_ALPHABET:
                letter_idx = RUSSIAN_ALPHABET.index(ch_upper)
                block = idx // L
                pos_in_block = idx % L
                base_char = clean_key[pos_in_block]
                base_idx = base_indices[pos_in_block]
                key_char_idx = (base_idx + block) % 33
                key_char = RUSSIAN_ALPHABET[key_char_idx]
                prog_key_letters.append(key_char)
                result_char = RUSSIAN_ALPHABET[(letter_idx + key_char_idx) % 33]
                typ = "буква"
                tree_steps.insert("", "end", values=(
                    pos, ch, typ, base_char, block, pos_in_block,
                    key_char, letter_idx, result_char
                ))
                idx += 1
            else:
                tree_steps.insert("", "end", values=(
                    pos, ch, "не буква", "-", "-", "-", "-", "-", ch
                ))

        if idx == 0:
            ttk.Label(frame_steps, text="Нет русских букв для обработки").pack()
        else:
            prog_key_str = "".join(prog_key_letters)
            ttk.Label(frame_steps, text=f"Прогрессивный ключ: {prog_key_str}",
                      font=("Segoe UI", 10, "bold"), foreground="blue").pack(pady=5)

        # Большая таблица Виженера 33×33
        frame_big = ttk.LabelFrame(window, text="Таблица Виженера (русский алфавит, 33×33)")
        frame_big.pack(pady=15, padx=20, fill="both", expand=True)

        columns_big = list(RUSSIAN_ALPHABET)
        tree_big = ttk.Treeview(frame_big, columns=columns_big, show="headings", height=20)
        tree_big.heading("#0", text="Буква текста")
        tree_big.column("#0", width=80, anchor="center")
        for c in columns_big:
            tree_big.heading(c, text=c)
            tree_big.column(c, width=40, anchor="center")

        h_scroll = ttk.Scrollbar(frame_big, orient="horizontal", command=tree_big.xview)
        v_scroll = ttk.Scrollbar(frame_big, orient="vertical", command=tree_big.yview)
        tree_big.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        tree_big.grid(row=0, column=0, sticky="nsew")
        h_scroll.grid(row=1, column=0, sticky="ew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        frame_big.grid_rowconfigure(0, weight=1)
        frame_big.grid_columnconfigure(0, weight=1)

        for i, letter in enumerate(RUSSIAN_ALPHABET):
            row_values = []
            for j in range(len(RUSSIAN_ALPHABET)):
                idx = (i + j) % 33
                row_values.append(RUSSIAN_ALPHABET[idx])
            tree_big.insert("", "end", text=letter, values=row_values)

        ttk.Label(window, text="Таблица Виженера (без учёта прогрессивного сдвига). Прогрессивный сдвиг прибавляется к индексу ключа.",
                  font=("Segoe UI", 10)).pack(pady=5)


if __name__ == "__main__":
    app = CryptoApp()
    app.mainloop()