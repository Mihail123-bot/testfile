import tkinter as tk

# Create the main window
root = tk.Tk()
root.title("Message Window")

# Set window size
root.geometry("300x100")

# Create a label with the message
label = tk.Label(root, text="You're dumb", font=("Arial", 16))
label.pack(pady=20)

# Run the GUI application
root.mainloop()
