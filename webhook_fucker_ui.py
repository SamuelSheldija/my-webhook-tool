import tkinter as tk
from tkinter import ttk, messagebox
import requests
import time
import threading
import asyncio
import discord
from discord.ext import commands
from queue import Queue

# Theme definitions
THEMES = {
    "Dark": {
        "bg": "#2C2F33", "fg": "#FFFFFF", "button_bg": "#7289DA", "button_fg": "#FFFFFF",
        "entry_bg": "#36393F", "progress_fg": "#7289DA", "progress_bg": "#23272A",
        "graph_bg": "#23272A", "graph_line": "#FF5555", "active_bg": "#5B6EAE"
    },
    "Light": {
        "bg": "#FFFFFF", "fg": "#2C2F33", "button_bg": "#7289DA", "button_fg": "#FFFFFF",
        "entry_bg": "#F2F3F5", "progress_fg": "#7289DA", "progress_bg": "#DCDDDE",
        "graph_bg": "#F2F3F5", "graph_line": "#FF5555", "active_bg": "#5B6EAE"
    },
    "Hacker": {
        "bg": "#0A0F0A", "fg": "#00FF00", "button_bg": "#00CC00", "button_fg": "#FFFFFF",
        "entry_bg": "#1A2A1A", "progress_fg": "#00FF00", "progress_bg": "#0A0F0A",
        "graph_bg": "#1A2A1A", "graph_line": "#00FF00", "active_bg": "#00AA00"
    },
    "Neon": {
        "bg": "#1A0033", "fg": "#FF00FF", "button_bg": "#00FFFF", "button_fg": "#000000",
        "entry_bg": "#2A0044", "progress_fg": "#00FFFF", "progress_bg": "#1A0033",
        "graph_bg": "#2A0044", "graph_line": "#FF00FF", "active_bg": "#00CCCC"
    }
}

# Webhook Backend Functions
def is_valid_url(url):
    return url.startswith("https://discord.com/api/webhooks/") and len(url.strip()) > 50

def send_message(webhook_url, message):
    if not is_valid_url(webhook_url):
        return "Invalid URL"
    try:
        response = requests.post(webhook_url, json={"content": message})
        return "Sent" if response.status_code == 204 else f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"

def spam_webhook(webhook_url, message, count, rate, callback):
    if not is_valid_url(webhook_url):
        return "Invalid URL"
    for i in range(count):
        result = send_message(webhook_url, f"{message} #{i+1}")
        if "Error" in result:
            return result
        callback(i + 1, count)
        time.sleep(rate)
    return f"Spammed {count} times"

def delete_webhook(webhook_url):
    if not is_valid_url(webhook_url):
        return "Invalid URL"
    try:
        response = requests.delete(webhook_url)
        return "Deleted" if response.status_code == 204 else f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"

def nuke_webhook(webhook_url, message, count, rate, callback):
    spam_result = spam_webhook(webhook_url, message, count, rate, callback)
    if "Error" in spam_result:
        return spam_result
    delete_result = delete_webhook(webhook_url)
    return f"{spam_result}\n{delete_result}"

def run_webhook_action(urls, action, message, count, rate, callback):
    results = []
    total = len(urls) * (count if action in ["spam", "nuke"] else 1)
    progress = 0
    for url in urls:
        if action == "test":
            results.append(send_message(url, message))
            progress += 1
            callback(progress, total)
        elif action == "spam":
            def spam_callback(current, _):
                nonlocal progress
                progress = current
                callback(progress, total)
            results.append(spam_webhook(url, message, count, rate, spam_callback))
        elif action == "nuke":
            def nuke_callback(current, _):
                nonlocal progress
                progress = current
                callback(progress, total)
            results.append(nuke_webhook(url, message, count, rate, nuke_callback))
        elif action == "delete":
            results.append(delete_webhook(url))
            progress += 1
            callback(progress, total)
    return "\n".join(results)

# Raiding Bot Class with Intents
class RaidingBot(commands.Bot):
    def __init__(self, guild_id, channel_names, messages, rate, status_queue, *args, **kwargs):
        # Define the intents required for the bot
        intents = discord.Intents.default()
        intents.guilds = True  # Required to access guild information
        intents.messages = True  # Required to send messages
        super().__init__(command_prefix='!', intents=intents, *args, **kwargs)
        self.guild_id = guild_id
        self.channel_names = channel_names
        self.messages = messages
        self.rate = rate
        self.status_queue = status_queue

    async def on_ready(self):
        try:
            guild = self.get_guild(int(self.guild_id))
            if not guild:
                self.status_queue.put("Guild not found")
                await self.close()
                return
            await self.create_channels(guild, self.channel_names)
            channels = [channel for channel in guild.text_channels if channel.name in self.channel_names]
            await self.spam_messages(channels, self.messages, self.rate)
            self.status_queue.put("Raid complete")
        except Exception as e:
            self.status_queue.put(f"Error: {e}")
        finally:
            await self.close()

    async def create_channels(self, guild, channel_names):
        for name in channel_names:
            await guild.create_text_channel(name)

    async def spam_messages(self, channels, messages, rate):
        for channel in channels:
            for message in messages:
                await channel.send(message)
                await asyncio.sleep(rate)

# UI Functions
def apply_theme(theme_name):
    global current_theme
    current_theme = theme_name
    theme = THEMES[theme_name]
    root.config(bg=theme["bg"])
    for widget, wtype in all_widgets:
        if wtype == "frame":
            widget.config(bg=theme["bg"])
        elif wtype == "label":
            widget.config(bg=theme["bg"], fg=theme["fg"])
        elif wtype == "button":
            widget.config(bg=theme["button_bg"], fg=theme["button_fg"], activebackground=theme["active_bg"])
        elif wtype == "entry":
            widget.config(bg=theme["entry_bg"], fg=theme["fg"], insertbackground=theme["fg"])
        elif wtype == "text":
            widget.config(bg=theme["entry_bg"], fg=theme["fg"])
        elif wtype == "canvas":
            widget.config(bg=theme["graph_bg"])
            draw_graph(0)
    style = ttk.Style()
    style.configure("Horizontal.TProgressbar", background=theme["progress_fg"], troughcolor=theme["progress_bg"])
    root.update_idletasks()

def toggle_mode():
    if mode_var.get() == "Webhook":
        webhook_frame.pack(pady=10, padx=10, fill="x")
        raiding_frame.forget()
        webhook_action_frame.pack()
        raiding_action_frame.forget()
    else:
        raiding_frame.pack(pady=10, padx=10, fill="x")
        webhook_frame.forget()
        raiding_action_frame.pack()
        webhook_action_frame.forget()

def clear():
    url_entry.delete(0, tk.END)
    msg_entry.delete(0, tk.END)
    count_entry.delete(0, tk.END)
    rate_entry.delete(0, tk.END)
    rate_entry.insert(0, "0.5")
    token_entry.delete(0, tk.END)
    guild_id_entry.delete(0, tk.END)
    channel_names_entry.delete(0, tk.END)
    raid_messages_entry.delete(0, tk.END)
    raid_rate_entry.delete(0, tk.END)
    raid_rate_entry.insert(0, "0.5")
    output_text.delete(1.0, tk.END)
    progress_var.set(0)
    status_label.config(text="Ready")
    draw_graph(0)

def execute_webhook(action):
    urls = [u.strip() for u in url_entry.get().split(",") if u.strip()]
    msg = msg_entry.get().strip()
    count = 1 if action == "test" else None
    if action in ["spam", "nuke"]:
        try:
            count = int(count_entry.get())
            if count <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Count must be positive")
            return
    try:
        rate = float(rate_entry.get())
        if rate < 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Error", "Rate must be non-negative")
        return
    if not urls or not all(is_valid_url(u) for u in urls):
        messagebox.showerror("Error", "Invalid webhook URLs")
        return
    if action in ["test", "spam", "nuke"] and not msg:
        messagebox.showerror("Error", "Message required")
        return

    def callback(current, total):
        progress_var.set((current / total) * 100)
        draw_graph(int(current / len(urls)) if action in ["spam", "nuke"] else 0)

    def thread():
        status_label.config(text=f"{action.capitalize()}ing...")
        result = run_webhook_action(urls, action, msg, count, rate, callback)
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, result)
        status_label.config(text="Done")
        progress_var.set(0)
        draw_graph(0)

    threading.Thread(target=thread, daemon=True).start()

def execute_raid():
    global raid_active
    if raid_active:
        messagebox.showinfo("Raid in Progress", "A raid is already in progress.")
        return
    if not messagebox.askyesno("Confirm Raid", "Are you sure you want to raid the server? This action cannot be undone."):
        return
    raid_active = True
    token = token_entry.get().strip()
    guild_id = guild_id_entry.get().strip()
    channel_names = [name.strip() for name in channel_names_entry.get().split(",") if name.strip()]
    messages = [msg.strip() for msg in raid_messages_entry.get().split(",") if msg.strip()]
    try:
        rate = float(raid_rate_entry.get())
        if rate < 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Error", "Rate must be non-negative")
        raid_active = False
        return
    if not token or not guild_id or not channel_names or not messages:
        messagebox.showerror("Error", "All fields are required for raiding")
        raid_active = False
        return

    bot = RaidingBot(guild_id, channel_names, messages, rate, status_queue)

    def bot_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(bot.start(token))

    threading.Thread(target=bot_thread, daemon=True).start()

    def check_queue():
        while not status_queue.empty():
            message = status_queue.get()
            output_text.insert(tk.END, message + "\n")
        if raid_active:
            root.after(100, check_queue)
        else:
            status_label.config(text="Raid finished")

    check_queue()
    status_label.config(text="Raiding...")

def draw_graph(count):
    theme = THEMES[current_theme]
    graph_canvas.delete("all")
    graph_canvas.create_line(10, 100, 350, 100, fill=theme["fg"])
    graph_canvas.create_line(10, 100, 10, 10, fill=theme["fg"])
    if count > 0:
        step = 340 / max(count, 10)
        for i in range(min(count, 10)):
            x = 10 + i * step
            y = 100 - min((i + 1) * 9, 90)
            graph_canvas.create_line(x, 100, x, y, fill=theme["graph_line"], width=2)

def open_theme_menu():
    top = tk.Toplevel(root)
    top.title("Themes")
    top.geometry("200x150")
    top.config(bg=THEMES[current_theme]["bg"])
    var = tk.StringVar(value=current_theme)
    for theme in THEMES:
        tk.Radiobutton(top, text=theme, variable=var, value=theme, command=lambda: [apply_theme(var.get()), top.destroy()],
                       bg=THEMES[current_theme]["bg"], fg=THEMES[current_theme]["fg"],
                       selectcolor=THEMES[current_theme]["entry_bg"]).pack(anchor="w", padx=10, pady=5)

# UI Setup
root = tk.Tk()
root.title("Discord Tool")
root.geometry("400x850")
root.resizable(False, False)

current_theme = "Dark"
all_widgets = []
status_queue = Queue()
raid_active = False

main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True)
all_widgets.append((main_frame, "frame"))

title_label = tk.Label(main_frame, text="Discord Tool", font=("Arial", 18, "bold"))
title_label.pack(pady=10)
all_widgets.append((title_label, "label"))

mode_var = tk.StringVar(value="Webhook")
mode_frame = tk.Frame(main_frame)
mode_frame.pack(pady=5)
all_widgets.append((mode_frame, "frame"))

tk.Radiobutton(mode_frame, text="Webhook", variable=mode_var, value="Webhook", command=toggle_mode).pack(side="left", padx=10)
tk.Radiobutton(mode_frame, text="Raiding", variable=mode_var, value="Raiding", command=toggle_mode).pack(side="left", padx=10)

webhook_frame = tk.Frame(main_frame)
all_widgets.append((webhook_frame, "frame"))

tk.Label(webhook_frame, text="Webhook URLs (comma-separated):").pack(anchor="w")
url_entry = tk.Entry(webhook_frame, width=40)
url_entry.pack(fill="x", pady=2)
all_widgets.extend([(tk.Label(webhook_frame, text="Webhook URLs (comma-separated):"), "label"), (url_entry, "entry")])

tk.Label(webhook_frame, text="Message:").pack(anchor="w")
msg_entry = tk.Entry(webhook_frame, width=40)
msg_entry.pack(fill="x", pady=2)
all_widgets.extend([(tk.Label(webhook_frame, text="Message:"), "label"), (msg_entry, "entry")])

tk.Label(webhook_frame, text="Count (Spam/Nuke):").pack(anchor="w")
count_entry = tk.Entry(webhook_frame, width=10)
count_entry.pack(fill="x", pady=2)
all_widgets.extend([(tk.Label(webhook_frame, text="Count (Spam/Nuke):"), "label"), (count_entry, "entry")])

tk.Label(webhook_frame, text="Rate (seconds):").pack(anchor="w")
rate_entry = tk.Entry(webhook_frame, width=10)
rate_entry.insert(0, "0.5")
rate_entry.pack(fill="x", pady=2)
all_widgets.extend([(tk.Label(webhook_frame, text="Rate (seconds):"), "label"), (rate_entry, "entry")])

raiding_frame = tk.Frame(main_frame)
all_widgets.append((raiding_frame, "frame"))

tk.Label(raiding_frame, text="Bot Token:").pack(anchor="w")
token_entry = tk.Entry(raiding_frame, width=40, show="*")
token_entry.pack(fill="x", pady=2)
all_widgets.extend([(tk.Label(raiding_frame, text="Bot Token:"), "label"), (token_entry, "entry")])

tk.Label(raiding_frame, text="Server ID:").pack(anchor="w")
guild_id_entry = tk.Entry(raiding_frame, width=40)
guild_id_entry.pack(fill="x", pady=2)
all_widgets.extend([(tk.Label(raiding_frame, text="Server ID:"), "label"), (guild_id_entry, "entry")])

tk.Label(raiding_frame, text="Channel Names (comma-separated):").pack(anchor="w")
channel_names_entry = tk.Entry(raiding_frame, width=40)
channel_names_entry.pack(fill="x", pady=2)
all_widgets.extend([(tk.Label(raiding_frame, text="Channel Names (comma-separated):"), "label"), (channel_names_entry, "entry")])

tk.Label(raiding_frame, text="Messages (comma-separated):").pack(anchor="w")
raid_messages_entry = tk.Entry(raiding_frame, width=40)
raid_messages_entry.pack(fill="x", pady=2)
all_widgets.extend([(tk.Label(raiding_frame, text="Messages (comma-separated):"), "label"), (raid_messages_entry, "entry")])

tk.Label(raiding_frame, text="Rate (seconds):").pack(anchor="w")
raid_rate_entry = tk.Entry(raiding_frame, width=10)
raid_rate_entry.insert(0, "0.5")
raid_rate_entry.pack(fill="x", pady=2)
all_widgets.extend([(tk.Label(raiding_frame, text="Rate (seconds):"), "label"), (raid_rate_entry, "entry")])

action_frame = tk.Frame(main_frame)
action_frame.pack(pady=10)
all_widgets.append((action_frame, "frame"))

webhook_action_frame = tk.Frame(action_frame)
all_widgets.append((webhook_action_frame, "frame"))

test_btn = tk.Button(webhook_action_frame, text="Test", command=lambda: execute_webhook("test"))
spam_btn = tk.Button(webhook_action_frame, text="Spam", command=lambda: execute_webhook("spam"))
nuke_btn = tk.Button(webhook_action_frame, text="Nuke", command=lambda: execute_webhook("nuke"))
delete_btn = tk.Button(webhook_action_frame, text="Delete", command=lambda: execute_webhook("delete"))
for btn in [test_btn, spam_btn, nuke_btn, delete_btn]:
    btn.pack(side="left", padx=5)
    all_widgets.append((btn, "button"))

raiding_action_frame = tk.Frame(action_frame)
all_widgets.append((raiding_action_frame, "frame"))

raid_btn = tk.Button(raiding_action_frame, text="Raid", command=execute_raid)
raid_btn.pack(side="left", padx=5)
all_widgets.append((raid_btn, "button"))

clear_btn = tk.Button(action_frame, text="Clear", command=clear)
clear_btn.pack(pady=5)
all_widgets.append((clear_btn, "button"))

status_label = tk.Label(main_frame, text="Ready")
status_label.pack(pady=5)
all_widgets.append((status_label, "label"))

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(main_frame, variable=progress_var, maximum=100, length=360)
progress_bar.pack(pady=5)

output_text = tk.Text(main_frame, height=10, width=45)
output_text.pack(pady=10)
all_widgets.append((output_text, "text"))

graph_canvas = tk.Canvas(main_frame, width=360, height=120)
graph_canvas.pack(pady=10)
all_widgets.append((graph_canvas, "canvas"))

theme_btn = tk.Button(main_frame, text="Theme", command=open_theme_menu)
theme_btn.pack(pady=5)
all_widgets.append((theme_btn, "button"))

# Initial setup
apply_theme("Dark")
toggle_mode()
draw_graph(0)
root.mainloop()
