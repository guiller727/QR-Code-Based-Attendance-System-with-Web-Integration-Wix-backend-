import os
from tkinter import *
from PIL import Image, ImageTk
from tkinter import messagebox
from attendance_manager import build_gui

class Login:
    def __init__(self, root):
        self.root = root
        self.root.title("Login System for Attendace Tracker")
        self.root.geometry("1199x600+100+50")
        self.root.resizable(False, False)

        # Path to images
        script_dir = os.path.dirname(__file__)
        bg_path = os.path.join(script_dir, "images", "login_background.png")
        bt_path = os.path.join(script_dir, "images", "submit_button.png")

        # Load and display background image on left
        self.bg_image_raw = Image.open(bg_path).resize((600, 600))
        self.bg = ImageTk.PhotoImage(self.bg_image_raw)
        self.bg_label = Label(self.root, image=self.bg)
        self.bg_label.place(x=0, y=0, width=600, height=600)

        #AppIcon
        icon_img_path = os.path.join(script_dir, "images", "qr_icon.png")
        icon_image = PhotoImage(file=icon_img_path)
        self.root.iconphoto(False, icon_image)

        # Right side login panel
        login_frame = Frame(self.root, bg="white")
        login_frame.place(x=600, y=0, width=599, height=600)

        # Header
        Label(login_frame, text="LOG IN HERE", font=("Arial", 30, "bold underline"), bg="white", fg="black").place(x=160, y=100)
        Label(login_frame, text="Admin Log In Area", font=("Arial", 18), bg="white", fg="black").place(x=190, y=160)

        # Username
        Label(login_frame, text="USERNAME", font=("Arial", 12, "bold"), bg="white", fg="black").place(x=100, y=220)
        self.username = Entry(login_frame, font=("Arial", 12), bg="white", fg="black", bd=2, relief=SOLID)
        self.username.place(x=100, y=250, width=400, height=40)

        # Password
        Label(login_frame, text="PASSWORD", font=("Arial", 12, "bold"), bg="white", fg="black").place(x=100, y=310)
        self.password = Entry(login_frame, font=("Arial", 12), show="*", bg="white", fg="black", bd=2, relief=SOLID)
        self.password.place(x=100, y=340, width=400, height=40)

        # Show Password with custom styled checkbox
        self.show_password_var = BooleanVar(value=False)

        self.checkbox_border = Frame(login_frame, bg="black", highlightthickness=0)
        self.checkbox_border.place(x=100, y=390)

        self.checkbox_inner = Frame(self.checkbox_border, bg="white", padx=1, pady=1)
        self.checkbox_inner.pack()

        self.custom_checkbox = Checkbutton(
            self.checkbox_inner,
            text="Show Password",
            variable=self.show_password_var,
            command=self.toggle_password,
            bg="white", fg="black",
            font=("Arial", 10),
            activebackground="white",
            selectcolor="#D8BFD8",  # light purple inner color
            bd=0,
            highlightthickness=0
        )
        self.custom_checkbox.pack()

        # Load button image
        self.bt_image_raw = Image.open(bt_path).resize((200, 150))
        self.bt_image = ImageTk.PhotoImage(self.bt_image_raw)

        # Label acting as button
        self.login_button = Label(login_frame, image=self.bt_image, text="Login", compound="center",
                                  font=("Arial", 14, "bold"), fg="black", cursor="hand2", bg="white")
        self.login_button.place(x=200, y=407)

        # Click action
        self.login_button.bind("<Button-1>", lambda event: self.login_function())

        # Hover effect
        self.login_button.bind("<Enter>", lambda e: self.login_button.config(fg="white"))
        self.login_button.bind("<Leave>", lambda e: self.login_button.config(fg="black"))

        self.root.bind('<Return>', lambda event: self.login_function())
        self.username.focus_set()

    def toggle_password(self):
        if self.show_password_var.get():
            self.password.config(show="")
        else:
            self.password.config(show="*")

    def login_function(self):
        user = self.username.get()
        pwd = self.password.get()
        if user == "Admin" and pwd == "Admin":
            self.root.withdraw()
            attendance_window = build_gui(self.root)
            attendance_window.protocol("WM_DELETE_WINDOW", lambda: self.show_login(attendance_window))
            self.username.delete(0, END)
            self.password.delete(0, END)
        else:
            messagebox.showerror("Error", "Invalid username or password")
            self.username.delete(0, END)
            self.password.delete(0, END)
            self.username.focus_set()

    def show_login(self, window):
        window.destroy()
        self.root.deiconify()  # show login window again
        self.username.focus_set()

if __name__ == "__main__":
    root = Tk()
    app = Login(root)
    root.mainloop()
