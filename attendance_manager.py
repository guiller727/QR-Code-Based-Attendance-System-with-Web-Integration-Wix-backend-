import os
import threading
import time
import webbrowser
from collections import defaultdict
from datetime import datetime, timedelta
from tkinter import filedialog, font, messagebox, ttk, PhotoImage
import tkinter as tk

import qrcode  # pip install qrcode[pil]
import requests
from dotenv import load_dotenv  # pip install python-dotenv
from openpyxl import Workbook
from PIL import Image, ImageTk

load_dotenv()

# Wix backend base URL
BASE_URL = os.getenv("BASE_URL")

def fetch_attendance():
    response = requests.get(f"{BASE_URL}/getAttendance")
    return response.json().get("items", [])

def format_time(created_raw):
    try:
        created_dt = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        created_dt += timedelta(hours=8)
        return created_dt.strftime("%m-%d-%Y %I:%M %p")
    except:
        return "N/A"

def build_gui(parent):
    root = tk.Toplevel(parent)
    root.title("Attendance Tracker")
    root.geometry("1199x600+100+50")
    root.resizable(False, False) 

    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_img_path = os.path.join(script_dir, "assets", "qr_icon.png")
    icon_image = PhotoImage(file=icon_img_path)
    root.iconphoto(False, icon_image)

    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill="both", expand=True)

    control_frame = tk.Frame(main_frame, bg="white", width=180)
    control_frame.pack(side="left", fill="y", padx=20, pady=20)
    control_frame.pack_propagate(False)
    content_frame = ttk.Frame(main_frame)
    content_frame.pack(side="right", fill="both", expand=True)
    content_frame.pack()

    search_frame = tk.Frame(content_frame)
    search_frame.pack(fill="x", padx=5, pady=(0, 10), anchor="w")

    search_var = tk.StringVar()

    def clear_search():
        search_var.set("")
        populate_table()

    def is_valid_date(date_string):
        """Check if a date string matches any of the valid date formats."""
        date_formats = [
            "%m-%d-%Y",   # 04-06-2025
            "%m-%d-%y",   # 04-06-25
            "%m-%d-%Y",   # 4-6-2025
            "%m-%d-%y",   # 4-6-25
            "%m %d %y",   # 4 6 25
            "%m %d %Y",   # 4 6 2025
        ]
        for date_format in date_formats:
            try:
                datetime.strptime(date_string, date_format)
                return True
            except ValueError:
                continue
        return False

    def search_table(event=None):
        query = search_var.get().lower().strip()
        if not query:
            populate_table()
            return

        filtered = []
        if is_valid_date(query):
            # Try all formats to parse the date correctly
            query_date = None
            for fmt in ["%m-%d-%Y", "%m-%d-%y", "%m %d %y", "%m %d %Y"]:
                try:
                    query_date = datetime.strptime(query, fmt)
                    break
                except ValueError:
                    continue

            if query_date:
                for entry in fetch_attendance():
                    created_dt = entry.get("_createdDate", "")
                    if created_dt:
                        record_date = datetime.fromisoformat(created_dt.replace("Z", "+00:00")) + timedelta(hours=8)
                        if record_date.date() == query_date.date():
                            filtered.append(entry)
        else:
            for entry in fetch_attendance():
                for key in ["full_name_last_first_mi", "student_id", "selfie_link"]:
                    if query in str(entry.get(key, "")).lower():
                        filtered.append(entry)
                        break

        populate_table(filtered)

    tk.Label(search_frame, text="Search:", font=("Arial", 11, "bold")).pack(side="left", padx=(5, 2))
    search_entry = ttk.Entry(search_frame, textvariable=search_var, font=("Arial", 11), width=30)
    search_entry.pack(side="left", padx=2)
    search_entry.bind("<Return>", search_table)

    btn_search = tk.Button(search_frame, cursor="hand2", text="Search", command=search_table,
                           bg="#726eff", fg="white", font=("Arial", 10, "bold"), relief="flat")
    btn_search.pack(side="left", padx=5)

    btn_clear = tk.Button(search_frame, cursor="hand2", text="Clear", command=clear_search,
                          bg="#726eff", fg="white", font=("Arial", 10, "bold"), relief="flat")
    btn_clear.pack(side="left", padx=2)

    # Date-Time Label beside Clear button
    datetime_label = tk.Label(search_frame, text="", font=("Arial", 10, "bold"), fg="black")
    datetime_label.pack(side="left", padx=10)

    def update_datetime():
        now = datetime.now()
        day_name = now.strftime("%A")  # e.g., Monday
        formatted = now.strftime(f"%m-%d-%Y %I:%M %p ({day_name})")
        datetime_label.config(text=formatted)
        root.after(1000, update_datetime)  # update every second

    update_datetime()  # initial call

    columns = ("ID", "Name", "Student ID", "Selfie Link", "Submitted (Date & Time)", "Days Present")
    global tree
    style = ttk.Style()

    style.configure("Treeview.Heading",
                    background="gray",
                    font=("Helvetica", 10, "bold"))

    
    tree = ttk.Treeview(content_frame, columns=columns, show="headings", height=20, selectmode="extended", style="Treeview")

    for col in columns:
        tree.heading(col, text=col)  

    def sort_tree(column, reverse=False, is_datetime=False):
        data = [(tree.set(k, column), k) for k in tree.get_children('')]

        if is_datetime:
            def parse_dt(val):
                try:
                    return datetime.strptime(val, "%m-%d-%Y %I:%M %p")
                except:
                    return datetime.min
            data.sort(key=lambda t: parse_dt(t[0]), reverse=reverse)
        else:
            data.sort(key=lambda t: t[0].lower(), reverse=reverse)

        for index, (val, k) in enumerate(data):
            tree.move(k, '', index)

    # Popup menus
    name_menu = tk.Menu(tree, tearoff=0)
    name_menu.add_command(label="Sort A-Z", command=lambda: sort_tree("Name", reverse=False))
    name_menu.add_command(label="Sort Z-A", command=lambda: sort_tree("Name", reverse=True))

    time_menu = tk.Menu(tree, tearoff=0)
    time_menu.add_command(label="Sort Ascending", command=lambda: sort_tree("Submitted (Date & Time)", reverse=False, is_datetime=True))
    time_menu.add_command(label="Sort Descending", command=lambda: sort_tree("Submitted (Date & Time)", reverse=True, is_datetime=True))

    # Header right-click event binding
    def show_header_menu(event):
        region = tree.identify_region(event.x, event.y)
        column = tree.identify_column(event.x)
        col_name = tree.heading(column)['text']
        if region == "heading":
            if col_name == "Name":
                name_menu.post(event.x_root, event.y_root)
            elif col_name == "Submitted (Date & Time)":
                time_menu.post(event.x_root, event.y_root)

    tree.bind("<Button-3>", show_header_menu)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=190, anchor="center")
    tree.column("ID", width=0, stretch=False)

    scrollbar_y = ttk.Scrollbar(content_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar_y.set)

    tree.pack(side="left", fill="both", expand=True, padx=(0, 10))
    scrollbar_y.pack(side="right", fill="y")

    def populate_table(data=None):
        if data is None:
            data = fetch_attendance()  # fallback if no data passed

        tree.delete(*tree.get_children())

        latest_by_student = {}
        history_by_student = defaultdict(list)

        for entry in data:
            student_id = entry.get("student_id", "N/A")
            created_dt = entry.get("_createdDate", "")
            history_by_student[student_id].append(entry)
            # Only keep latest
            if student_id not in latest_by_student or created_dt > latest_by_student[student_id].get("_createdDate", ""):
                latest_by_student[student_id] = entry

        for student_id, entry in latest_by_student.items():
            name = entry.get("full_name_last_first_mi", "N/A")
            raw_link = entry.get("selfie_link", "N/A")
            if raw_link.startswith("wix:image://v1/"):
                try:
                    filename = raw_link.split("wix:image://v1/")[1].split('/')[0]
                    selfie_link = f"https://static.wixstatic.com/media/{filename}"
                except:
                    selfie_link = "Invalid Wix Link"
            else:
                selfie_link = raw_link

            timestamp = format_time(entry.get("_createdDate", ""))
            count = len(history_by_student[student_id])
            day_label = "day" if count == 1 else "days"
            tree.insert("", "end", values=(entry.get("_id"), name, student_id, selfie_link, timestamp, f"{count} {day_label}"))

    last_refresh_time = [0]

    def refresh_data(root, show_toast_flag=False):
        import time
        now = time.time()
        if now - last_refresh_time[0] < 1: 
            return  
        last_refresh_time[0] = now

        def do_refresh():
            data = fetch_attendance()
            root.after(0, lambda: populate_table(data))  
            if show_toast_flag:
                root.after(100, lambda: show_toast(root, "Refreshed"))
        threading.Thread(target=do_refresh).start()

    def show_toast(root, message):
        toast = tk.Label(root, text=message, bg="green", fg="white", font=("Arial", 12),
                         relief="solid", bd=1, padx=10, pady=5)
        toast.place(relx=0.6, rely=0.9, anchor="center")
        root.after(1000, toast.destroy)

    def export_data():
        file = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not file:
            return
        wb = Workbook()
        ws = wb.active
        ws.title = "Attendance"
        ws.append(["Name", "Student ID", "Selfie Link", "Submitted (Date & Time)", "Days Present"])
        for row_id in tree.get_children():
            values = tree.item(row_id, "values")
            ws.append(values[1:])
        wb.save(file)
        messagebox.showinfo("Exported", f"Data exported to {file}")

    def set_window_icon(window):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_img_path = os.path.join(script_dir, "assets", "qr_icon.png")
        try:
            icon_image = tk.PhotoImage(file=icon_img_path)
            window.iconphoto(False, icon_image)
            window._icon_image = icon_image  # Prevent garbage collection
        except Exception as e:
            print(f"Could not set window icon: {e}")

    def show_custom_warning(parent, title="Warning"):
        warning_window = tk.Toplevel(parent)
        warning_window.title(title)
        warning_window.geometry("350x150")
        warning_window.resizable(False, False)
        set_window_icon(warning_window)  # Reuse your existing function

        #warning_window.grab_set()
        warning_window.configure(bg="white")

        tk.Label(warning_window, text=title, font=("Arial", 11, "bold"), fg="black", bg="white").pack(pady=(10, 5))

        tk.Button(warning_window, text="OK", command=warning_window.destroy,
                bg="#726eff", fg="white", font=("Arial", 10, "bold"),
                relief="flat", cursor="hand2", padx=10, pady=5).pack(pady=10)

    def show_expiry_popup(parent):
        popup = tk.Toplevel(parent)
        popup.title("QR Code Expiry")
        popup.geometry("300x150")
        popup.configure(bg="white")
        popup.resizable(False, False)  
        set_window_icon(popup)
            
        tk.Label(popup, text="QR Code Expiry (minutes):", font=("Arial", 11), bg="white").pack(pady=10)
        
        entry = tk.Entry(popup, font=("Arial", 11))
        entry.insert(0, "5")  # Default to 5 minutes
        entry.pack()
        
        def generate():
            try:
                mins = int(entry.get())
                popup.destroy()
                show_qr_code(parent, mins)
            except ValueError:
                messagebox.showerror("Invalid", "Please enter a valid number of minutes.")
        
        tk.Button(popup, text="Generate", command=generate, bg="#726eff", fg="white", font=("Arial", 10, "bold"), relief="flat").pack(pady=10)

    def show_qr_code(parent, expire_minutes):
        qr_window = tk.Toplevel(parent)
        qr_window.title("QR Code")
        qr_window.geometry("320x380")
        qr_window.configure(bg="white")
        qr_window.resizable(False, False)  
        
        set_window_icon(qr_window)
    
        expiry_time = datetime.now() + timedelta(minutes=expire_minutes)
        expiry_str = expiry_time.strftime("%I:%M %p")
        
        tk.Label(qr_window, text=f"Expires at: {expiry_str}", font=("Arial", 10), bg="white").pack(pady=10)
        
        # Generate the QR code
        qr = qrcode.make("https://c23-1148-284.wixsite.com/attendly")
        qr_img = ImageTk.PhotoImage(qr.resize((250, 250)))
        qr_label = tk.Label(qr_window, image=qr_img, bg="white")
        qr_label.pack()
        qr_window.image = qr_img  # Keep reference

        def check_expiry():
            current_time = datetime.now()
            if current_time >= expiry_time:
                qr_window.destroy()
                messagebox.showinfo("QR Expired", "This QR code has expired.")
            else:
                qr_window.after(1000, check_expiry)  # Check every second

        check_expiry()  

    def add_data(root):
        def save():
            data = {
                "name": name_var.get(),
                "studentId": id_var.get(),
                "selfieLink": link_var.get()
            }
            requests.post(f"{BASE_URL}/addAttendance", json=data)
            win.destroy()
            refresh_data(root, show_toast_flag=True)

        win = tk.Toplevel(root)
        win.title("Add Record")
        win.geometry("350x300")
        win.resizable(False, False)
        set_window_icon(win)

        frame = ttk.Frame(win, padding=30)
        frame.pack(fill="both", expand=True)

        name_var = tk.StringVar()
        id_var = tk.StringVar()
        link_var = tk.StringVar()

        bold_font = font.Font(weight="bold", size=10)

        ttk.Label(frame, text="Name", font=bold_font).pack(anchor="w", pady=(0, 5))
        ttk.Entry(frame, textvariable=name_var).pack(fill="x", pady=(0, 15))

        ttk.Label(frame, text="Student ID", font=bold_font).pack(anchor="w", pady=(0, 5))
        ttk.Entry(frame, textvariable=id_var).pack(fill="x", pady=(0, 15))

        ttk.Label(frame, text="Selfie Link", font=bold_font).pack(anchor="w", pady=(0, 5))
        ttk.Entry(frame, textvariable=link_var).pack(fill="x", pady=(0, 20))

        styled_button("Save", save, parent=frame, stretch=True, cursor="hand2")

    def edit_data(root):
        selected = tree.focus()
        if not selected:
            show_custom_warning(root, "Select a row to edit.")
            return
        
        item = tree.item(selected)['values']

        def update():
            updated = {
                "id": item[0],
                "name": name_var.get(),
                "studentId": id_var.get(),
                "selfieLink": link_var.get()
            }
            requests.put(f"{BASE_URL}/updateAttendance", json=updated)
            win.destroy()
            refresh_data(root, show_toast_flag=True)

        win = tk.Toplevel(root)
        win.title("Edit Record")
        win.geometry("350x300")
        win.resizable(False, False)
        set_window_icon(win)

        frame = ttk.Frame(win, padding=30)
        frame.pack(fill="both", expand=True)

        name_var = tk.StringVar(value=item[1])
        id_var = tk.StringVar(value=item[2])
        link_var = tk.StringVar(value=item[3])

        bold_font = font.Font(weight="bold", size=10)

        ttk.Label(frame, text="Name", font=bold_font).pack(anchor="w", pady=(0, 5))
        ttk.Entry(frame, textvariable=name_var).pack(fill="x", pady=(0, 15))

        ttk.Label(frame, text="Student ID", font=bold_font).pack(anchor="w", pady=(0, 5))
        ttk.Entry(frame, textvariable=id_var).pack(fill="x", pady=(0, 15))

        ttk.Label(frame, text="Selfie Link", font=bold_font).pack(anchor="w", pady=(0, 5))
        ttk.Entry(frame, textvariable=link_var).pack(fill="x", pady=(0, 20))

        styled_button("Update", update, parent=frame, stretch=True, cursor="hand2")

    def delete_data(root):
        selected_items = tree.selection()
        if not selected_items:
            show_custom_warning(root, "Select one or more rows to delete.")
            return
        
        if not messagebox.askyesno("Confirm", f"Are you sure you want to delete {len(selected_items)} record(s)?"):
            return

        def perform_deletion():
            for item_id in selected_items:
                record = tree.item(item_id)['values']
                try:
                    requests.delete(f"{BASE_URL}/deleteAttendance?id={record[0]}")
                except Exception as e:
                    print(f"Error deleting {record[0]}: {e}")
            refresh_data(root, show_toast_flag=True)

        threading.Thread(target=perform_deletion).start()

    def confirm_exit(attendance_window, login_root):
        dialog = tk.Toplevel(attendance_window)
        dialog.title("Logout Confirmation")
        dialog.geometry("420x130")  # Adjust size for better fit
        dialog.resizable(False, False)
        dialog.grab_set()  # Make modal
        set_window_icon(dialog)

        tk.Label(dialog, text="Do you want to logout or exit the app?", font=("Arial", 12)).pack(pady=10)

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10, padx=10, fill='x')

        # Inner frame to center buttons
        inner_frame = tk.Frame(button_frame)
        inner_frame.pack()

        def on_logout():
            dialog.destroy()
            attendance_window.destroy()  # Close attendance window
            login_root.deiconify() 
            login_root.show()

        def on_exit():
            dialog.destroy()
            login_root.destroy()         # Exit entire app
            import sys
            sys.exit()

        def on_cancel():
            dialog.destroy()             # Close dialog only

        small_font = ("Arial", 10, "bold")

        btn_logout = tk.Button(
            inner_frame, text="Yes", command=on_logout,
            bg="#726eff", fg="white", font=small_font, relief="flat",
            bd=0, cursor="hand2", padx=12, pady=6
        )
        btn_cancel = tk.Button(
            inner_frame, text="No", command=on_cancel,
            bg="#726eff", fg="white", font=small_font, relief="flat",
            bd=0, cursor="hand2", padx=12, pady=6
        )
        btn_exit = tk.Button(
            inner_frame, text="Exit", command=on_exit,
            bg="#726eff", fg="white", font=small_font, relief="flat",
            bd=0, cursor="hand2", padx=12, pady=6
        )

        # Pack buttons side-by-side with some padding
        btn_logout.pack(side="left", padx=8)
        btn_cancel.pack(side="left", padx=8)
        btn_exit.pack(side="left", padx=8)

    def styled_button(text, command, parent=None, stretch=False, **kwargs):
        btn = tk.Button(
            parent or control_frame,
            text=text,
            command=command,
            bg="#726eff",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            height=2,
            width=14,
            bd=0,
            **kwargs  
        )
        if stretch:
            btn.pack(pady=15, anchor="center", fill="x", padx=20)
        else:
            btn.pack(pady=15, anchor="center")
        return btn

    styled_button("QR-Code", lambda: show_expiry_popup(root), cursor="hand2")
    styled_button("Add", lambda: add_data(root), cursor="hand2")
    styled_button("Edit", lambda: edit_data(root), cursor="hand2")
    styled_button("Remove", lambda: delete_data(root), cursor="hand2")
    styled_button("Export", export_data, cursor="hand2")
    styled_button("Refresh", lambda: refresh_data(root, show_toast_flag=True), cursor="hand2")
    styled_button("Logout", lambda: confirm_exit(root, parent), cursor="hand2")

    def on_tree_double_click(event):
        item_id = tree.focus()
        if not item_id:
            return
        values = tree.item(item_id, 'values')
        col = tree.identify_column(event.x)

        if col == '#4':  # Selfie link
            if values[3].startswith("http"):
                webbrowser.open(values[3])
        elif col == '#6':  # Days present
            show_attendance_popup(values[2])  # student_id

    tree.bind("<Double-1>", on_tree_double_click)

    def show_attendance_popup(student_id):
        data = fetch_attendance()
        all_entries = [d for d in data if d.get("student_id") == student_id]
        all_entries.sort(key=lambda x: x.get("_createdDate", ""), reverse=True)

        win = tk.Toplevel()
        win.title("Attendance History")
        win.geometry("600x350")
        win.configure(bg="white")
        win.resizable(False, False)

        tk.Label(win, text=f"Attendance History for {student_id}",
                font=("Arial", 12, "bold"), bg="white").pack(pady=10)

        frame = tk.Frame(win, bg="white")
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        header = tk.Frame(frame, bg="white")
        header.pack(fill="x")
        tk.Label(header, text="Submitted (Date & Time)", font=("Arial", 10, "bold"), width=30, anchor="w", bg="white").pack(side="left")
        tk.Label(header, text="Selfie Link", font=("Arial", 10, "bold"), width=60, anchor="w", bg="white").pack(side="left")

        canvas = tk.Canvas(frame, borderwidth=0, bg="white", height=200)
        scroll_y = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll_y.set)

        canvas.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        # Add each row
        for entry in all_entries:
            time_str = format_time(entry.get("_createdDate", ""))
            raw_link = entry.get("selfie_link", "N/A")
            if raw_link.startswith("wix:image://v1/"):
                try:
                    filename = raw_link.split("wix:image://v1/")[1].split('/')[0]
                    link = f"https://static.wixstatic.com/media/{filename}"
                except:
                    link = "Invalid Wix Link"
            else:
                link = raw_link

            row = tk.Frame(scrollable_frame, bg="white")
            row.pack(fill="x", pady=2)

            tk.Label(row, text=time_str, font=("Arial", 10), width=30, anchor="w", bg="white").pack(side="left")

            link_lbl = tk.Label(row, text=link, font=("Arial", 10, "underline"), fg="blue", cursor="hand2", bg="white", anchor="w", justify="left", wraplength=400)
            link_lbl.pack(side="left", fill="x", expand=True)

            def open_link(event, url=link):
                if url.startswith("http"):
                    webbrowser.open(url)
                    
            link_lbl.bind("<Button-1>", open_link)

        styled_button("Close", win.destroy, parent=win, stretch=False, cursor="hand2")

    populate_table()
    return root

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  
    app = build_gui(root)
    app.mainloop()
