import tkinter as tk
from tkinter import ttk, font, messagebox
import requests
import time
import threading

# Theme definitions with distinct colors
THEMES = {
    "Dark": {
        "bg": "#1C1C1C",  # Dark background
        "fg": "#FFFFFF",  # White text
        "accent": "#00FF00",  # Bright green for buttons
        "secondary_bg": "#333333",  # Dark gray for frames
        "text_bg": "#4D4D4D",  # Medium gray for text areas
        "graph_bg": "#333333",
        "graph_line": "#FF0000",  # Red graph line
        "progress_fg": "#00FF00",
        "progress_bg": "#333333",
        "button_active": "#00CC00",  # Darker green on click
    },
    "Light": {
        "bg": "#FFFFFF",  # White background
        "fg": "#000000",  # Black text
        "accent": "#0000FF",  # Blue for buttons
        "secondary_bg": "#F0F0F0",  # Light gray for frames
        "text_bg": "#FFFFFF",
        "graph_bg": "#F0F0F0",
        "graph_line": "#FF0000",
        "progress_fg": "#0000FF",
        "progress_bg": "#DCDDDE",
        "button_active": "#0000CC",  # Darker blue on click
    },
    "Hacker Green": {
        "bg": "#000000",  # Black background
        "fg": "#00FF00",  # Green text
        "accent": "#00FF00",
        "secondary_bg": "#001100",
        "text_bg": "#001100",
        "graph_bg": "#001100",
        "graph_line": "#00FF00",
        "progress_fg": "#00FF00",
        "progress_bg": "#000000",
        "button_active": "#00CC00",
    },
    "Neon": {
        "bg": "#000000",
        "fg": "#FF00FF",  # Magenta text
        "accent": "#00FFFF",  # Cyan for buttons
        "secondary_bg": "#111111",
        "text_bg": "#111111",
        "graph_bg": "#111111",
        "graph_line": "#FF00FF",
        "progress_fg": "#00FFFF",
        "progress_bg": "#111111",
        "button_active": "#00CCCC",
    },
}

# Backend functions
def is_valid_url(url):
    return url.startswith("https://discord.com/api/webhooks/") and len(url.strip()) > 50

def delete_webhook(webhook_url):
    if not is_valid_url(webhook_url):
        return "Invalid webhook URL."
    try:
        response = requests.delete(webhook_url)
        return "Webhook deleted successfully." if response.status_code == 204 else f"Failed to delete: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def send_message(webhook_url, message):
    if not is_valid_url(webhook_url):
        return "Invalid webhook URL."
    try:
        payload = {"content": message}
        response = requests.post(webhook_url, json=payload)
        return "Message sent successfully." if response.status_code == 204 else f"Failed to send: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def spam_webhook(webhook_url, message, count, rate_limit, progress_callback):
    if not is_valid_url(webhook_url):
        return "Invalid webhook URL."
    if count <= 0:
        return "Count must be positive."
    for i in range(count):
        try:
            payload = {"content": f"{message} - Spam #{i+1}"}
            response = requests.post(webhook_url, json=payload)
            if response.status_code != 204:
                return f"Spam failed at #{i+1}: {response.status_code}"
            progress_callback(i + 1, count)
            time.sleep(rate_limit)
        except Exception as e:
            return f"Error: {str(e)}"
    return f"Spammed {count} messages."

def nuke_webhook(webhook_url, message, count, rate_limit, progress_callback):
    spam_result = spam_webhook(webhook_url, message, count, rate_limit, progress_callback)
    if "failed" in spam_result.lower() or "invalid" in spam_result.lower():
        return spam_result
    delete_result = delete_webhook(webhook_url)
    return f"{spam_result}\n{delete_result}"

def multi_webhook_action(webhook_urls, action, message=None, count=None, rate_limit=0.5, progress_callback=None):
    results = []
    total_actions = len(webhook_urls) if action in ["delete", "test"] else len(webhook_urls) * (count + (1 if action == "nuke" else 0))
    current_action = 0
    for url in webhook_urls:
        if action == "delete":
            results.append(delete_webhook(url))
            current_action += 1
            progress_callback(current_action, total_actions)
        elif action == "spam":
            def spam_progress(current, total):
                progress_callback(current_action + current, total_actions)
            result = spam_webhook(url, message, count, rate_limit, spam_progress)
            results.append(result)
            current_action += count
        elif action == "nuke":
            def nuke_progress(current, total):
                progress_callback(current_action + current, total_actions)
            result = nuke_webhook(url, message, count, rate_limit, nuke_progress)
            results.append(result)
            current_action += count + 1
            progress_callback(current_action, total_actions)  # Update progress after delete
        elif action == "test":
            results.append(send_message(url, message))
            current_action += 1
            progress_callback(current_action, total_actions)
    return "\n".join(results)

# UI Setup
root = tk.Tk()
root.title("Webhook Tool")
root.geometry("400x900")
root.resizable(False, False)

# Fonts
roboto_bold = font.Font(family="Arial", size=16, weight="bold")
roboto_regular = font.Font(family="Arial", size=12)

# Global variables
current_theme = "Dark"
style = ttk.Style()

# Apply theme function
def apply_theme(theme_name):
    global current_theme
    try:
        current_theme = theme_name if theme_name in THEMES else "Dark"
        theme = THEMES[current_theme]
        root.config(bg=theme["bg"])
        root.update_idletasks()  # Force UI update
        
        # Header
        header_frame.config(bg=theme["secondary_bg"])
        header_label.config(bg=theme["secondary_bg"], fg=theme["fg"])
        settings_btn.config(bg=theme["accent"], fg=theme["fg"], activebackground=theme["button_active"])
        
        # Input Frame
        input_frame.config(bg=theme["secondary_bg"])
        for widget in input_frame.winfo_children():
            widget.config(bg=theme["secondary_bg"], fg=theme["fg"])
            if isinstance(widget, tk.Entry):
                widget.config(bg=theme["text_bg"], fg=theme["fg"], insertbackground=theme["fg"])
        
        # Button Frame
        button_frame.config(bg=theme["secondary_bg"])
        for widget in button_frame.winfo_children():
            widget.config(bg=theme["accent"], fg=theme["fg"], activebackground=theme["button_active"])
        
        # Status Frame
        status_frame.config(bg=theme["secondary_bg"])
        status_label.config(bg=theme["secondary_bg"], fg=theme["fg"])
        
        # Progress Frame
        progress_frame.config(bg=theme["secondary_bg"])
        style.configure("Custom.Horizontal.TProgressbar", background=theme["progress_fg"], troughcolor=theme["progress_bg"])
        progress_bar.configure(style="Custom.Horizontal.TProgressbar")
        
        # Output Frame
        output_frame.config(bg=theme["secondary_bg"])
        output_text.config(bg=theme["text_bg"], fg=theme["fg"])
        
        # Graph Frame
        graph_frame.config(bg=theme["secondary_bg"])
        graph_canvas.config(bg=theme["graph_bg"])
        
        draw_graph(0)  # Redraw graph with new theme
        root.update()  # Ensure all changes are rendered
        print(f"Theme '{current_theme}' applied successfully.")
    except Exception as e:
        print(f"Error applying theme: {e}")
        messagebox.showerror("Theme Error", f"Failed to apply theme: {e}")

# Header
header_frame = tk.Frame(root)
header_frame.pack(fill="x", pady=10)
header_label = tk.Label(header_frame, text="Webhook Tool", font=roboto_bold)
header_label.pack(pady=5)
settings_btn = tk.Button(header_frame, text="⚙", font=roboto_regular, command=lambda: open_settings(), width=2)
settings_btn.place(x=360, y=5)

# Input Section
input_frame = tk.Frame(root)
input_frame.pack(fill="x", padx=20, pady=5)

tk.Label(input_frame, text="Webhook URLs (comma-separated):", font=roboto_regular).pack(pady=5)
url_entry = tk.Entry(input_frame, width=40, font=roboto_regular)
url_entry.pack(pady=5)

tk.Label(input_frame, text="Message:", font=roboto_regular).pack(pady=5)
msg_entry = tk.Entry(input_frame, width=40, font=roboto_regular)
msg_entry.pack(pady=5)

tk.Label(input_frame, text="Spam Count:", font=roboto_regular).pack(pady=5)
count_entry = tk.Entry(input_frame, width=10, font=roboto_regular)
count_entry.pack(pady=5)

tk.Label(input_frame, text="Rate Limit (seconds):", font=roboto_regular).pack(pady=5)
rate_entry = tk.Entry(input_frame, width=10, font=roboto_regular)
rate_entry.insert(0, "0.5")
rate_entry.pack(pady=5)

# Buttons
button_frame = tk.Frame(root)
button_frame.pack(fill="x", padx=20, pady=5)

test_btn = tk.Button(button_frame, text="Test", font=roboto_regular, command=lambda: run_action("test"))
test_btn.pack(side="left", padx=5)
spam_btn = tk.Button(button_frame, text="Spam", font=roboto_regular, command=lambda: run_action("spam"))
spam_btn.pack(side="left", padx=5)
nuke_btn = tk.Button(button_frame, text="Nuke", font=roboto_regular, command=lambda: run_action("nuke"))
nuke_btn.pack(side="left", padx=5)
delete_btn = tk.Button(button_frame, text="Delete", font=roboto_regular, command=lambda: run_action("delete"))
delete_btn.pack(side="left", padx=5)
clear_btn = tk.Button(button_frame, text="Clear", font=roboto_regular, command=lambda: clear_fields())
clear_btn.pack(side="left", padx=5)

# Status
status_frame = tk.Frame(root)
status_frame.pack(fill="x", padx=20, pady=5)
status_label = tk.Label(status_frame, text="Ready", font=roboto_regular)
status_label.pack(pady=5)

# Progress
progress_frame = tk.Frame(root)
progress_frame.pack(fill="x", padx=20, pady=5)
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100, length=360, style="Custom.Horizontal.TProgressbar")
progress_bar.pack()

# Output Section
output_frame = tk.Frame(root)
output_frame.pack(fill="x", padx=20, pady=5)
output_text = tk.Text(output_frame, height=15, width=45, font=roboto_regular, wrap="word")
output_text.pack(pady=5)

# Graph Section
graph_frame = tk.Frame(root)
graph_frame.pack(fill="x", padx=20, pady=5)
graph_canvas = tk.Canvas(graph_frame, width=340, height=110)
graph_canvas.pack(pady=10)

# Settings Menu
def open_settings():
    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("250x150")
    settings_window.config(bg=THEMES[current_theme]["bg"])
    
    tk.Label(settings_window, text="Theme:", font=roboto_regular, bg=THEMES[current_theme]["bg"], fg=THEMES[current_theme]["fg"]).pack(pady=10)
    theme_var = tk.StringVar(value=current_theme)
    theme_menu = ttk.Combobox(settings_window, textvariable=theme_var, values=list(THEMES.keys()), state="readonly")
    theme_menu.pack(pady=5)
    
    def apply_settings():
        global current_theme
        current_theme = theme_var.get()
        apply_theme(current_theme)
        settings_window.destroy()
    
    tk.Button(settings_window, text="Apply", font=roboto_regular, command=apply_settings, bg=THEMES[current_theme]["accent"], fg=THEMES[current_theme]["fg"]).pack(pady=10)

# Clear Fields
def clear_fields():
    url_entry.delete(0, tk.END)
    msg_entry.delete(0, tk.END)
    count_entry.delete(0, tk.END)
    rate_entry.delete(0, tk.END)
    rate_entry.insert(0, "0.5")
    output_text.delete(1.0, tk.END)
    progress_var.set(0)
    status_label.config(text="Ready")
    draw_graph(0)

# Run Action
def run_action(action):
    urls = [url.strip() for url in url_entry.get().split(",") if url.strip()]
    msg = msg_entry.get().strip()
    count = 1 if action == "test" else None
    if action in ["spam", "nuke"]:
        try:
            count = int(count_entry.get())
            if count <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Spam count must be a positive integer.")
            return
    try:
        rate_limit = float(rate_entry.get())
        if rate_limit < 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Error", "Rate limit must be a non-negative number.")
        return
    
    if not urls or not all(is_valid_url(url) for url in urls):
        messagebox.showerror("Error", "Enter valid Discord webhook URLs.")
        return
    if action in ["test", "spam", "nuke"] and not msg:
        messagebox.showerror("Error", "Message cannot be empty.")
        return

    def progress_callback(current, total):
        progress_var.set((current / total) * 100)
        root.update_idletasks()  # Ensure progress bar updates in real-time
    
    def thread_func():
        status_label.config(text="Processing...")
        result = multi_webhook_action(urls, action, msg, count, rate_limit, progress_callback)
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, result)
        progress_var.set(0)
        status_label.config(text="Done!")
        if action in ["spam", "nuke"]:
            draw_graph(count)
    
    threading.Thread(target=thread_func, daemon=True).start()

# Draw Graph
def draw_graph(count):
    graph_canvas.delete("all")
    theme = THEMES[current_theme]
    graph_canvas.create_line(10, 100, 330, 100, fill=theme["fg"])  # X-axis
    graph_canvas.create_line(10, 100, 10, 10, fill=theme["fg"])     # Y-axis
    if count > 0:
        step = 320 / max(count, 1)
        points = [(10 + i * step, 100 - min((i + 1) * 10, 90)) for i in range(min(count, 10))]
        for i in range(len(points) - 1):
            graph_canvas.create_line(points[i][0], points[i][1], points[i+1][0], points[i+1][1], fill=theme["graph_line"], width=2)

# Initial setup
apply_theme(current_theme)
draw_graph(0)

# Start the app
root.mainloop()