import tkinter as tk
from tkinter import ttk, messagebox
import calendar
from datetime import date, timedelta

# Русские названия месяцев (calendar.month_name даёт английские)
MONTH_NAMES = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
               "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]


class DatePickerDialog:
    # Простой календарь-диалог (без внешних зависимостей)
    def __init__(self, parent, initial_date=None):
        self.top = tk.Toplevel(parent)
        self.top.transient(parent)
        self.top.grab_set()
        self.top.title("Выберите дату")
        self.top.geometry("300x340")

        if initial_date is None:
            initial_date = date.today()

        self.year = initial_date.year
        self.month = initial_date.month
        self.selected_date = initial_date

        self.create_widgets()
        self.update_calendar()

    def create_widgets(self):
        # Управление годом/месяцем
        ctrl_frame = ttk.Frame(self.top)
        ctrl_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(ctrl_frame, text="<", width=3, command=self.prev_year).pack(side="left")
        self.lbl_year = ttk.Label(ctrl_frame, text=str(self.year), font=("Arial", 11, "bold"))
        self.lbl_year.pack(side="left", padx=8)
        ttk.Button(ctrl_frame, text=">", width=3, command=self.next_year).pack(side="left")

        ttk.Separator(ctrl_frame, orient="vertical").pack(side="left", fill="y", padx=15, pady=2)

        ttk.Button(ctrl_frame, text="<<", width=3, command=self.prev_month).pack(side="left")
        self.lbl_month = ttk.Label(ctrl_frame, text=MONTH_NAMES[self.month - 1], font=("Arial", 11))
        self.lbl_month.pack(side="left", padx=8)
        ttk.Button(ctrl_frame, text=">>", width=3, command=self.next_month).pack(side="left")

        # Сетка календаря
        cal_frame = ttk.Frame(self.top)
        cal_frame.pack(fill="both", expand=True, padx=10, pady=5)

        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        for i, d in enumerate(days):
            ttk.Label(cal_frame, text=d, font=("Arial", 9, "bold"), anchor="center").grid(row=0, column=i, padx=2, pady=4)

        self.day_buttons = []
        for r in range(1, 7):
            for c in range(7):
                btn = tk.Button(cal_frame, text="", width=4, height=1, relief="flat", bg="#f5f5f5",
                                command=lambda r=r, c=c: self.on_day_click(r, c))
                btn.grid(row=r, column=c, padx=2, pady=2)
                self.day_buttons.append(btn)

        ok_frame = ttk.Frame(self.top)
        ok_frame.pack(pady=10)
        ttk.Button(ok_frame, text="OK", command=self.on_ok).pack()

    def update_calendar(self):
        first_weekday, days_in_month = calendar.monthrange(self.year, self.month)

        for btn in self.day_buttons:
            btn.config(text="", bg="#f5f5f5", fg="black")

        day_idx = 1
        for row in range(1, 7):
            for col in range(7):
                cell = (row - 1) * 7 + col
                if cell >= first_weekday and day_idx <= days_in_month:
                    btn = self.day_buttons[cell]
                    btn.config(text=str(day_idx))
                    if (self.year == self.selected_date.year and
                            self.month == self.selected_date.month and
                            day_idx == self.selected_date.day):
                        btn.config(bg="#2563eb", fg="white")
                    day_idx += 1

        self.lbl_year.config(text=str(self.year))
        self.lbl_month.config(text=MONTH_NAMES[self.month - 1])

    def prev_year(self):
        self.year -= 1
        self.update_calendar()

    def next_year(self):
        self.year += 1
        self.update_calendar()

    def prev_month(self):
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        self.update_calendar()

    def next_month(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self.update_calendar()

    def on_day_click(self, row, col):
        idx = (row - 1) * 7 + col
        btn = self.day_buttons[idx]
        text = btn.cget("text")
        if not text:
            return
        day = int(text)
        self.selected_date = date(self.year, self.month, day)
        self.update_calendar()

    def on_ok(self):
        self.top.destroy()


def get_days_in_month(year, month):
    return calendar.monthrange(year, month)[1]


def format_money(value):
    return f"{value:,.2f} \u20bd"


def set_entry_date(entry, new_date):
    # В read-only поле вставка игнорируется, поэтому снимаем readonly на время записи
    entry.config(state="normal")
    entry.delete(0, tk.END)
    entry.insert(0, new_date.strftime("%Y-%m-%d"))
    entry.config(state="readonly")


def parse_date_entry(entry):
    try:
        return date.fromisoformat(entry.get())
    except Exception:
        return date.today()


def annuity_payment(balance, i, n, monthly_commission):
    # Аннуитет, внутри которого уже сидят проценты и комиссия
    if n <= 0:
        return balance + monthly_commission
    if i == 0:
        return balance / n + monthly_commission
    a_n = (1 - (1 + i) ** (-n)) / i
    return balance / a_n + monthly_commission


def calculate_schedule(principal, rate_annual, months, start_date, prepayments):
    i = rate_annual / 100 / 12            # месячная ставка для аннуитета
    daily_rate = rate_annual / 100 / 365  # дневная ставка: проценты от даты займа
    monthly_commission = principal * 0.01

    A = annuity_payment(principal, i, months, monthly_commission)

    balance = principal
    schedule = []
    prepay_index = 0
    prepayments_sorted = sorted(prepayments, key=lambda x: x["date"])
    payment_num = 1

    while balance > 0.001 and payment_num <= months * 2:
        # Платёж привязан к дню выдачи: 15-го — значит 15-го каждого месяца
        m_total = start_date.month - 1 + payment_num
        y = start_date.year + m_total // 12
        m = m_total % 12 + 1
        day = min(start_date.day, get_days_in_month(y, m))
        pay_date = date(y, m, day)

        # Проценты за фактические дни с даты займа (для первого платежа)
        # или с даты предыдущего платежа
        prev_date = start_date if payment_num == 1 else schedule[-1]["date"]
        days_accrued = (pay_date - prev_date).days
        if days_accrued <= 0:
            days_accrued = 1

        interest = balance * daily_rate * days_accrued
        commission = monthly_commission

        extra_prepayment = 0.0
        prepay_type = ""
        while prepay_index < len(prepayments_sorted) and prepayments_sorted[prepay_index]["date"] <= pay_date:
            extra_prepayment += prepayments_sorted[prepay_index]["amount"]
            prepay_type = prepayments_sorted[prepay_index]["type"]
            prepay_index += 1

        if extra_prepayment > 0:
            balance -= extra_prepayment
            if balance < 0:
                balance = 0.0
            if prepay_type == "payment" and balance > 0.001:
                remaining = months - payment_num
                A = annuity_payment(balance, i, remaining, monthly_commission)

        if balance <= interest + commission + 0.005:
            # Последний платёж: закрываем остаток точно в ноль
            payment = balance + interest + commission
            principal_part = balance
            A = payment
        else:
            payment = A
            principal_part = A - interest - commission

        balance_after = balance - principal_part
        if balance_after < 0:
            balance_after = 0.0

        schedule.append({
            "num": payment_num,
            "date": pay_date,
            "payment": payment,
            "interest": interest,
            "commission": commission,
            "principal_part": principal_part,
            "balance_after": balance_after,
            "prepayment": extra_prepayment,
            "prepay_type": prepay_type
        })

        balance = balance_after
        payment_num += 1

    return schedule, A


class CreditCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Кредитный калькулятор (Tkinter + календарь)")
        self.root.geometry("900x720")

        self.prepayment_frames = []
        self.create_widgets()

    def create_widgets(self):
        # --- Основные параметры ---
        main_frame = ttk.LabelFrame(self.root, text="Основные параметры кредита", padding=15)
        main_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(main_frame, text="Сумма кредита, руб.:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_principal = ttk.Entry(main_frame, width=20)
        self.entry_principal.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="Годовая ставка, %:").grid(row=0, column=2, sticky="w", pady=5)
        self.entry_rate = ttk.Entry(main_frame, width=10)
        self.entry_rate.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(main_frame, text="Срок, месяцев:").grid(row=0, column=4, sticky="w", pady=5)
        self.entry_months = ttk.Entry(main_frame, width=10)
        self.entry_months.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(main_frame, text="Дата выдачи:").grid(row=0, column=6, sticky="w", pady=5)
        self.entry_start = ttk.Entry(main_frame, width=12, state="readonly")
        self.entry_start.grid(row=0, column=7, padx=4, pady=5)
        set_entry_date(self.entry_start, date.today())
        ttk.Button(main_frame, text="\U0001F4C5", width=4, command=self.pick_start_date).grid(row=0, column=8, padx=2, pady=5)

        # --- Досрочные погашения ---
        pp_frame = ttk.LabelFrame(self.root, text="Досрочные погашения", padding=15)
        pp_frame.pack(fill="x", padx=10, pady=5)

        self.pp_container = ttk.Frame(pp_frame)
        self.pp_container.pack(fill="both", expand=True)

        btn_add = ttk.Button(pp_frame, text="+ Добавить досрочное погашение", command=self.add_prepayment)
        btn_add.pack(anchor="w", pady=5)

        # Кнопка расчёта
        calc_btn = ttk.Button(self.root, text="Рассчитать", command=self.run_calculation)
        calc_btn.pack(pady=10)

        # Результаты
        res_frame = ttk.LabelFrame(self.root, text="Результаты", padding=10)
        res_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.summary_label = ttk.Label(res_frame, text="", font=("Arial", 11, "bold"), wraplength=850)
        self.summary_label.pack(anchor="w")

        cols = ("№", "Дата", "Платёж", "Остаток долга", "Досрочно", "Тип")
        self.tree = ttk.Treeview(res_frame, columns=cols, show="headings", height=12)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")
        self.tree.column("Дата", width=110, anchor="w")
        self.tree.column("Платёж", width=130, anchor="e")
        self.tree.column("Остаток долга", width=130, anchor="e")
        self.tree.column("Досрочно", width=110, anchor="e")
        self.tree.pack(fill="both", expand=True, pady=10)

        scrollbar = ttk.Scrollbar(res_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def pick_start_date(self):
        initial = parse_date_entry(self.entry_start)
        dialog = DatePickerDialog(self.root, initial)
        self.root.wait_window(dialog.top)
        if hasattr(dialog, "selected_date"):
            set_entry_date(self.entry_start, dialog.selected_date)

    def add_prepayment(self):
        frame = ttk.Frame(self.pp_container)
        frame.pack(fill="x", pady=4)

        ttk.Label(frame, text="Дата:").pack(side="left", padx=4)
        entry_date = ttk.Entry(frame, width=12, state="readonly")
        entry_date.pack(side="left", padx=4)
        set_entry_date(entry_date, date.today())

        ttk.Button(frame, text="\U0001F4C5", width=4,
                   command=lambda e=entry_date: self.pick_prepay_date(e)).pack(side="left", padx=2, pady=2)

        ttk.Label(frame, text="Сумма, руб.:").pack(side="left", padx=4)
        entry_amount = ttk.Entry(frame, width=10)
        entry_amount.pack(side="left", padx=4)

        ttk.Label(frame, text="Тип:").pack(side="left", padx=4)
        combo_type = ttk.Combobox(frame, values=["Уменьшить срок", "Уменьшить платёж"],
                                  state="readonly", width=15)
        combo_type.current(0)
        combo_type.pack(side="left", padx=4)

        ttk.Button(frame, text="\u00d7", width=2,
                   command=lambda f=frame: self.remove_prepayment(f)).pack(side="left", padx=4)

        self.prepayment_frames.append({
            "frame": frame,
            "date": entry_date,
            "amount": entry_amount,
            "type": combo_type
        })

    def remove_prepayment(self, frame):
        frame.destroy()
        self.prepayment_frames = [p for p in self.prepayment_frames if p["frame"] != frame]

    def pick_prepay_date(self, entry):
        initial = parse_date_entry(entry)
        dialog = DatePickerDialog(self.root, initial)
        self.root.wait_window(dialog.top)
        if hasattr(dialog, "selected_date"):
            set_entry_date(entry, dialog.selected_date)

    def run_calculation(self):
        try:
            principal = float(self.entry_principal.get())
            rate_annual = float(self.entry_rate.get())
            months = int(self.entry_months.get())
            start_date = parse_date_entry(self.entry_start)
        except Exception:
            messagebox.showerror("Ошибка", "Проверьте основные параметры: все поля должны быть заполнены корректно.")
            return

        prepayments = []
        for p in self.prepayment_frames:
            try:
                amount = float(p["amount"].get())
                if amount <= 0:
                    continue
                prepayments.append({
                    "date": parse_date_entry(p["date"]),
                    "amount": amount,
                    "type": "term" if p["type"].get() == "Уменьшить срок" else "payment"
                })
            except Exception:
                continue

        schedule, A = calculate_schedule(principal, rate_annual, months, start_date, prepayments)
        if not schedule:
            messagebox.showwarning("Внимание", "График пуст — проверьте параметры.")
            return

        total_interest = sum(r["interest"] for r in schedule)
        total_commission = sum(r["commission"] for r in schedule)
        total_payments = sum(r["payment"] for r in schedule)
        total_prepayments = sum(p["amount"] for p in prepayments)

        summary_text = (
            f"Сумма кредита: {format_money(principal)}\n"
            f"Годовая ставка: {rate_annual}%\n"
            f"Аннуитетный платёж (начальный): {format_money(A)}\n"
            f"Общая сумма выплат: {format_money(total_payments)}\n"
            f"Переплата (проценты + комиссия): {format_money(total_interest + total_commission)}\n"
            f"Проценты всего: {format_money(total_interest)}\n"
            f"Комиссия всего: {format_money(total_commission)}\n"
            f"Досрочно погашено: {format_money(total_prepayments)}\n"
            f"Фактический срок (платежей): {len(schedule)}"
        )
        self.summary_label.config(text=summary_text)

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in schedule:
            t = row["prepay_type"]
            t_text = "срок" if t == "term" else ("платёж" if t == "payment" else "")
            values = (
                row["num"],
                row["date"].strftime("%d.%m.%Y"),
                format_money(row["payment"]),
                format_money(row["balance_after"]),
                format_money(row["prepayment"]),
                t_text
            )
            self.tree.insert("", "end", values=values)


if __name__ == "__main__":
    root = tk.Tk()
    app = CreditCalculatorApp(root)
    root.mainloop()
