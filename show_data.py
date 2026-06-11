import tkinter as tk
from tkinter import ttk


DEFAULT_YINPIAN_DATA = [
    {"name": "烫狗脊", "digit_des": "15", "unit": "g", "opt_type": ""},
    {"name": "苦参", "digit_des": "15", "unit": "g", "opt_type": ""},
    {"name": "炒苍耳子", "digit_des": "10", "unit": "g", "opt_type": ""},
    {"name": "广金钱草", "digit_des": "30", "unit": "g", "opt_type": ""},
    {"name": "当归", "digit_des": "15", "unit": "g", "opt_type": ""},
    {"name": "白芷", "digit_des": "15", "unit": "g", "opt_type": ""},
    {"name": "五倍子", "digit_des": "10", "unit": "g", "opt_type": ""},
    {"name": "白鲜皮", "digit_des": "30", "unit": "g", "opt_type": ""},
    {"name": "菊苣", "digit_des": "20", "unit": "g", "opt_type": ""},
    {"name": "马齿苋", "digit_des": "30", "unit": "g", "opt_type": ""},
    {"name": "麦冬", "digit_des": "20", "unit": "g", "opt_type": ""},
]


def show_yinpian_grid(yinpian_data=None, title="处方饮片排列演示"):
    yinpian_data = yinpian_data or DEFAULT_YINPIAN_DATA

    root = tk.Tk()
    root.title(title)
    root.geometry("760x420")

    main_frame = ttk.Frame(root, padding=12)
    main_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(main_frame, text="饮片排列效果", font=("Microsoft YaHei UI", 14, "bold")).pack(anchor=tk.W)

    grid_frame = ttk.Frame(main_frame, padding=(0, 12, 0, 0))
    grid_frame.pack(fill=tk.BOTH, expand=True)

    columns_per_row = 4
    for col in range(columns_per_row):
        grid_frame.columnconfigure(col, weight=1, minsize=150)

    for index, yinpian_json in enumerate(yinpian_data):
        row = index // columns_per_row
        col = index % columns_per_row
        opt_type = yinpian_json.get("opt_type") or ""
        text = "{}{}{}{}".format(
            yinpian_json.get("name", ""),
            yinpian_json.get("digit_des", ""),
            yinpian_json.get("unit", ""),
            opt_type,
        )
        label = ttk.Label(
            grid_frame,
            text=text,
            anchor=tk.CENTER,
            relief=tk.GROOVE,
            padding=12,
            font=("Microsoft YaHei UI", 11),
        )
        label.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)

    root.mainloop()


def run_demo(yinpian_data=None):
    show_yinpian_grid(yinpian_data)


if __name__ == "__main__":
    run_demo()
