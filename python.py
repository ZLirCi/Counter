import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, filedialog
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import base64

FILE_NAME = "expenses.enc"
HIGH_EXPENSE_THRESHOLD = 1000  # hint for large expenses
ENCRYPT_KEY = 42  # key for XOR encryption


# ------------------- Encryption -------------------
def encrypt(text):
    """Simple text encryption using XOR + base64"""
    encoded = ''.join(chr(ord(c) ^ ENCRYPT_KEY) for c in text)
    return base64.b64encode(encoded.encode('utf-8')).decode('utf-8')


def decrypt(text):
    """Decryption"""
    try:
        decoded = base64.b64decode(text.encode('utf-8')).decode('utf-8')
        return ''.join(chr(ord(c) ^ ENCRYPT_KEY) for c in decoded)
    except Exception:
        return ""


# ------------------- File handling -------------------
def load_expenses():
    expenses = []
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            for line in file:
                decrypted_line = decrypt(line.strip())
                parts = decrypted_line.split(",")
                if len(parts) == 4:
                    date, name, category, amount = parts
                    expenses.append([date, name, category, float(amount)])
    except FileNotFoundError:
        pass
    return expenses


def save_expenses(expenses):
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        for e in expenses:
            line = f"{e[0]},{e[1]},{e[2]},{e[3]}"
            file.write(encrypt(line) + "\n")


# ------------------- GUI -------------------
class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Трекер витрат")
        self.expenses = load_expenses()

        # Table
        self.tree = ttk.Treeview(root, columns=("date", "name", "category", "amount"), show="headings")
        self.tree.heading("date", text="Дата")
        self.tree.heading("name", text="Назва")
        self.tree.heading("category", text="Категорія")
        self.tree.heading("amount", text="Сума (грн)")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Summary
        self.total_label = tk.Label(root, text="")
        self.total_label.pack(pady=5)

        # Buttons
        frame = tk.Frame(root)
        frame.pack(pady=10)
        tk.Button(frame, text="Додати", command=self.add_expense).pack(side=tk.LEFT, padx=3)
        tk.Button(frame, text="Редагувати", command=self.edit_expense).pack(side=tk.LEFT, padx=3)
        tk.Button(frame, text="Видалити", command=self.delete_expense).pack(side=tk.LEFT, padx=3)
        tk.Button(frame, text="Фільтр по даті", command=self.filter_by_date).pack(side=tk.LEFT, padx=3)
        tk.Button(frame, text="Пошук", command=self.search_expense).pack(side=tk.LEFT, padx=3)
        tk.Button(frame, text="Сортувати", command=self.sort_table).pack(side=tk.LEFT, padx=3)
        tk.Button(frame, text="Графік категорії", command=self.plot_categories).pack(side=tk.LEFT, padx=3)
        tk.Button(frame, text="Графік дати", command=self.plot_dates).pack(side=tk.LEFT, padx=3)
        tk.Button(frame, text="Назад", command=self.show_all).pack(side=tk.LEFT, padx=3)


        self.show_all()

    # ------------------- Table -------------------
    def show_all(self, expenses=None):
        if expenses is None:
            expenses = self.expenses

        for row in self.tree.get_children():
            self.tree.delete(row)

        total = 0
        for e in expenses:
            self.tree.insert("", tk.END, values=e)
            total += e[3]

        self.total_label.config(text=f"💰 Загальна сума: {total:.2f} грн")

    # ------------------- CRUD -------------------
    def add_expense(self):
        name = simpledialog.askstring("Додати витрату", "На що витратив гроші?")
        if not name:
            return
        category = simpledialog.askstring("Категорія", "Категорія витрати:")
        if not category:
            return
        while True:
            amount_str = simpledialog.askstring("Сума", "Скільки витратив? (тільки число)")
            if amount_str is None:
                return
            try:
                amount = float(amount_str)
                break
            except ValueError:
                messagebox.showerror("Помилка", "Введіть число!")

        if amount > HIGH_EXPENSE_THRESHOLD:
            messagebox.showwarning("Увага!", f"Великий витрата: {amount} грн")

        date = datetime.now().strftime("%d.%m.%Y")
        self.expenses.append([date, name, category, amount])
        save_expenses(self.expenses)
        self.show_all()

    def delete_expense(self):
        selected = self.tree.selection()
        if not selected:
            return
        index = self.tree.index(selected[0])
        if messagebox.askyesno("Видалити", "Впевнені, що хочете видалити?"):
            self.expenses.pop(index)
            save_expenses(self.expenses)
            self.show_all()

    def edit_expense(self):
        selected = self.tree.selection()
        if not selected:
            return
        index = self.tree.index(selected[0])
        e = self.expenses[index]

        name = simpledialog.askstring("Редагувати назву", "Назва витрати:", initialvalue=e[1])
        if not name:
            return
        category = simpledialog.askstring("Редагувати категорію", "Категорія:", initialvalue=e[2])
        if not category:
            return
        while True:
            amount_str = simpledialog.askstring("Редагувати суму", "Сума:", initialvalue=str(e[3]))
            if amount_str is None:
                return
            try:
                amount = float(amount_str)
                break
            except ValueError:
                messagebox.showerror("Помилка", "Введіть число!")

        if amount > HIGH_EXPENSE_THRESHOLD:
            messagebox.showwarning("Увага!", f"Великий витрата: {amount} грн")

        self.expenses[index] = [e[0], name, category, amount]
        save_expenses(self.expenses)
        self.show_all()

    # ------------------- Filter and search -------------------
    def filter_by_date(self):
        start = simpledialog.askstring("Фільтр", "Введіть початкову дату (дд.мм.рррр):")
        end = simpledialog.askstring("Фільтр", "Введіть кінцеву дату (дд.мм.рррр):")
        if not start or not end:
            return

        try:
            start_dt = datetime.strptime(start, "%d.%m.%Y")
            end_dt = datetime.strptime(end, "%d.%m.%Y")
        except ValueError:
            messagebox.showerror("Помилка", "Неправильний формат дати!")
            return

        filtered = [e for e in self.expenses if start_dt <= datetime.strptime(e[0], "%d.%m.%Y") <= end_dt]
        self.show_all(filtered)

    def search_expense(self):
        query = simpledialog.askstring("Пошук", "Введіть назву або категорію:")
        if not query:
            return
        filtered = [e for e in self.expenses if query.lower() in e[1].lower() or query.lower() in e[2].lower()]
        self.show_all(filtered)

    # ------------------- Sorting -------------------
    def sort_table(self):
        choice = simpledialog.askstring("Сортування", "Сортувати по (дата/сума/категорія):")
        if not choice:
            return
        choice = choice.lower()
        if choice == "дата":
            self.expenses.sort(key=lambda x: datetime.strptime(x[0], "%d.%m.%Y"))
        elif choice == "сума":
            self.expenses.sort(key=lambda x: x[3], reverse=True)
        elif choice == "категорія":
            self.expenses.sort(key=lambda x: x[2].lower())
        else:
            messagebox.showerror("Помилка", "Невірний вибір!")
            return
        self.show_all()

    # ------------------- Charts -------------------
    def plot_categories(self):
        if not self.expenses:
            messagebox.showinfo("Графік", "Немає витрат для побудови графіка")
            return
        cat_sums = defaultdict(float)
        for e in self.expenses:
            cat_sums[e[2]] += e[3]
        categories = list(cat_sums.keys())
        amounts = list(cat_sums.values())
        plt.figure(figsize=(6, 6))
        plt.pie(amounts, labels=categories, autopct='%1.1f%%')
        plt.title("Витрати по категоріях")
        plt.tight_layout()
        plt.show()

    def plot_dates(self):
        if not self.expenses:
            messagebox.showinfo("Графік", "Немає витрат для побудови графіка")
            return
        date_sums = defaultdict(float)
        for e in self.expenses:
            date_sums[e[0]] += e[3]
        dates = sorted(date_sums.keys(), key=lambda d: datetime.strptime(d, "%d.%m.%Y"))
        amounts = [date_sums[d] for d in dates]
        plt.figure(figsize=(8, 4))
        plt.bar(dates, amounts, color='skyblue')
        plt.xlabel("Дата")
        plt.ylabel("Сума витрат")
        plt.title("Витрати по датах")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()


# ------------------- Run -------------------
root = tk.Tk()
app = ExpenseTrackerApp(root)
root.mainloop()