---
name: python-tkinter-asyncio-desktop
description: Build a native-looking desktop GUI application using Python's built-in tkinter and asyncio, without heavy dependencies like PyQt. Handles cross-thread UI updates, async backend tasks, and a splash screen.
agent_created: true
---

# Python tkinter + asyncio 桌面 GUI 构建

This skill is used when a user asks to turn a Python-based CLI tool or Agent system into a desktop GUI application, especially when they want to avoid heavy GUI frameworks (PyQt, Electron) and keep the runtime lightweight.

## When to use

- Converting a Python CLI tool into a desktop window application.
- Building a GUI that needs to run long-running async tasks (network calls, AI inference, file processing) without freezing the UI.
- Targeting Windows users who prefer double-click `.bat` launchers.
- Avoiding extra binary dependencies beyond the Python standard library.

## Key design decisions

- **Use tkinter / ttk**: Already included with Python on Windows, macOS, and most Linux distributions. No extra pip install required.
- **Do NOT call tkinter widget methods from a background thread**: tkinter is not thread-safe. Always route UI updates back to the main thread.
- **Run an asyncio event loop in a dedicated daemon thread**: This lets the GUI remain responsive while coroutines perform network/model calls.
- **Use a `queue.Queue` for cross-thread UI updates**: Safer and more explicit than `root.after(0, ...)` from another thread.
- **Provide a splash screen**: Long initialization (loading models, checking APIs) is shown to the user instead of a blank window.
- **Page-based navigation**: A sidebar switches between functional views (chat, settings, status, etc.).

## Implementation template

The minimal reusable structure is:

```python
import asyncio
import concurrent.futures
import queue
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk
from typing import Callable, Coroutine

class AsyncTkApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._ui_queue: queue.Queue = queue.Queue()
        self.loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._loop_thread.start()
        self._pending_futures: list = []
        self._schedule_ui_poll()
        self._schedule_future_poll()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def submit(self, coro: Coroutine) -> concurrent.futures.Future:
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        self._pending_futures.append(future)
        return future

    def run_in_main_thread(self, func: Callable, *args, **kwargs):
        self._ui_queue.put((func, args, kwargs))

    def _schedule_ui_poll(self):
        self.root.after(50, self._poll_ui_queue)

    def _poll_ui_queue(self):
        try:
            while True:
                func, args, kwargs = self._ui_queue.get_nowait()
                func(*args, **kwargs)
        except queue.Empty:
            pass
        self._schedule_ui_poll()

    def _schedule_future_poll(self):
        self.root.after(100, self._poll_futures)

    def _poll_futures(self):
        still_pending = []
        for future in self._pending_futures:
            if future.done():
                try:
                    future.result()
                except Exception as e:
                    self._on_async_error(e)
            else:
                still_pending.append(future)
        self._pending_futures = still_pending
        self._schedule_future_poll()

    def _on_async_error(self, exc: Exception):
        from tkinter import messagebox
        messagebox.showerror("Background task error", f"{type(exc).__name__}: {exc}")
```

A concrete desktop app then inherits `AsyncTkApp` and:

1. Builds a splash screen in `__init__`.
2. Submits an async `init()` coroutine to load backend modules.
3. Calls `self.run_in_main_thread(self._hide_splash)` when ready.
4. Builds the main UI with a sidebar and page frames.

## Navigation pattern

- Store pages in `self.pages: dict[str, tk.Frame]`.
- `_show_page(page_name)` calls `pack_forget()` on all pages and `pack()` on the selected one.
- Highlight the active sidebar button by changing its background color.

## Chat page pattern

- Use a `scrolledtext.ScrolledText` for the conversation log.
- Use `Text` tags for user / assistant bubbles (different margins and background colors).
- Set the widget to `state=tk.DISABLED` after inserting messages to prevent user editing.
- Bind `<Return>` to send and `<Shift-Return>` to insert a newline.

## Windows launchers

- Write `.bat` files using `newline="\r\n"` in Python to avoid LF line endings that crash Windows batch `if/else` parsing.
- Typical desktop launcher:

```bat
@echo off
chcp 65001 >nul
cd /d "C:\Path\To\Project"
.venv\Scripts\python.exe -m mypackage.gui_main
```

## Testing in a headless environment

- Do not call `root.mainloop()` in tests.
- Manually pump events with `root.update()` / `root.update_idletasks()` in a loop.
- Keep a timeout so tests do not hang if the async backend stalls.

## Common pitfalls

- Calling `widget.config()` or `update_idletasks()` from the asyncio thread directly will deadlock or crash on Windows. Always go through `run_in_main_thread` or the equivalent queue.
- `tkinter.messagebox` must be called from the main thread. Route errors through the same queue.
- Heavy synchronous imports inside the async thread are fine, but any widget access must be in the main thread.
- Ensure the `.bat` file is saved with CRLF line endings; otherwise Windows `cmd.exe` fails to parse multi-line blocks.
