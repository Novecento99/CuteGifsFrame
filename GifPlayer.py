import os
import random
import tkinter as tk
from PIL import Image, ImageTk
import time
from cv2 import VideoCapture, cvtColor, COLOR_BGR2RGB, resize, CAP_PROP_FPS
import json
import pyautogui  # <-- Use pyautogui instead of pyinput

pyautogui.FAILSAFE = False  # Disable PyAutoGUI fail-safe


class GifsFrame:
    def __init__(self, folder_path, interval):
        self.folder_path = folder_path
        self.interval = interval
        self.gif_files = [
            f for f in os.listdir(folder_path) if f.endswith((".gif", ".GIF", ".mp4"))
        ]
        self.current_gif = None
        self.running = True
        self.stats_file = os.path.join(folder_path, "media_stats.json")
        self.play_counts = self.load_stats()

        # Initialize Tkinter window
        self.root = tk.Tk()
        self.root.title("Digital Frame")
        self.root.geometry("250x250")  # Set initial window size
        self.root.attributes("-topmost", True)  # Always stay on top
        self.root.resizable(True, True)  # Disable window resizing
        self.label = tk.Label(self.root)
        self.label.pack(fill=tk.BOTH, expand=True)
        self._resize_after_id = None  # For debouncing resize events
        self.root.bind("<Configure>", self.on_resize)
        self.current_frame_index = 0  # Track current frame for resizing
        self.load_random_frames()
        self.display_frames()

    def save_stats(self, stats=None):
        if stats is None:
            stats = self.play_counts
        try:
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2)
        except Exception as e:
            print(f"Error saving stats: {e}")

    def load_stats(self):
        # Always recreate stats from zero
        stats = {f: 0 for f in self.gif_files}
        self.save_stats(stats)
        return stats

    def on_resize(self, event):
        # Debounce rapid resize events
        if self._resize_after_id:
            self.root.after_cancel(self._resize_after_id)
        self._resize_after_id = self.root.after(150, self.reload_current_media)

    def load_gif(self, gif_path):
        self.current_gif = Image.open(gif_path)
        self.frames = []
        self.durations = []  # Store frame durations

        width, height = (
            self.root.winfo_width(),
            self.root.winfo_height(),
        )  # Get current window size
        print(width, height)
        try:
            while True:
                frame = self.current_gif.copy()
                orig_w, orig_h = frame.size
                # Calculate scale to fit inside window while preserving aspect ratio
                scale = min(width / orig_w, height / orig_h)
                new_w, new_h = int(orig_w * scale), int(orig_h * scale)
                frame = frame.resize((new_w, new_h), Image.LANCZOS)
                # Create yellow background and paste centered
                bg = Image.new("RGB", (width, height), (240, 240, 240))
                x = (width - new_w) // 2
                y = (height - new_h) // 2
                bg.paste(frame, (x, y), frame if frame.mode == "RGBA" else None)
                frame = ImageTk.PhotoImage(bg)
                self.frames.append(frame)
                duration = self.current_gif.info.get(
                    "duration", 40
                )  # Default to 40ms if not specified
                self.durations.append(duration / 1000.0)  # Convert to seconds
                self.current_gif.seek(len(self.frames))  # Move to the next frame
        except EOFError:
            pass  # End of GIF frames

    def load_mp4(self, video_path):
        self.video_path = video_path  # Store for reload
        self.video_capture = VideoCapture(video_path)
        self.frames = []
        self.durations = []
        fps = self.video_capture.get(CAP_PROP_FPS)  # Retrieve FPS of the video
        frame_duration = (
            1 / fps if fps > 0 else 1 / 30
        )  # Default to 30 FPS if FPS is invalid

        width, height = self.root.winfo_width(), self.root.winfo_height()
        print(width, height)
        while True:
            ret, frame = self.video_capture.read()
            if not ret:
                break
            frame = cvtColor(frame, COLOR_BGR2RGB)
            orig_h, orig_w, _ = frame.shape
            # Calculate scale to fit inside window while preserving aspect ratio
            scale = min(width / orig_w, height / orig_h)
            new_w, new_h = int(orig_w * scale), int(orig_h * scale)
            import numpy as np

            # Create yellow background
            bg = np.ones((height, width, 3), dtype=frame.dtype) * np.array(
                [240, 240, 240], dtype=frame.dtype
            )
            # Resize frame
            from cv2 import resize as cv2_resize

            resized_frame = cv2_resize(frame, (new_w, new_h))
            # Center the frame
            y = (height - new_h) // 2
            x = (width - new_w) // 2
            bg[y : y + new_h, x : x + new_w, :] = resized_frame
            frame = ImageTk.PhotoImage(Image.fromarray(bg.astype("uint8")))
            self.frames.append(frame)
            self.durations.append(frame_duration)  # Use the calculated frame duration
        self.video_capture.release()

    def load_random_frames(self):
        # Shuffle the list for better randomness and avoid immediate repeats
        if not hasattr(self, "last_media"):
            self.last_media = None
        available_files = self.gif_files.copy()
        if self.last_media in available_files and len(available_files) > 1:
            available_files.remove(self.last_media)
        random.shuffle(available_files)
        media_path = os.path.join(self.folder_path, available_files[0])
        self.last_media = available_files[0]
        self.play_counts[self.last_media] += 1  # Increment play count
        self.save_stats()
        print(f"\n[Random Media Selection]")
        print(f"Available media files: {len(self.gif_files)}")
        print(
            f"Selected: {os.path.basename(media_path)} (Played {self.play_counts[self.last_media]} times)"
        )
        self.root.update_idletasks()
        if media_path.endswith((".gif", ".GIF")):
            print("Loading GIF...")
            self.load_gif(media_path)
        elif media_path.endswith(".mp4"):
            print("Loading MP4 video...")
            self.load_mp4(media_path)

    def display_frames(self):
        def update_media():
            if self.running:
                self.load_random_frames()
                # Press "Scroll Lock" key to prevent focus loss
                # check if time is past 7 pm
                current_time = time.localtime()
                if current_time.tm_hour <= 19:  # 7 PM
                    print("oki doki")
                    pyautogui.press("scrolllock")
                    pyautogui.press("scrolllock")
                self.root.after(
                    self.interval * 1000, update_media
                )  # Schedule next update

        self.root.after(self.interval * 1000, update_media)  # Initial scheduling

        while True:
            for idx, (frame, duration) in enumerate(zip(self.frames, self.durations)):
                if not self.running:
                    break
                self.current_frame_index = idx  # Track current frame
                self.label.config(image=frame)
                self.root.update()
                time.sleep(duration)  # Use the frame-specific duration

    def reload_current_media(self):
        # Reload the current gif or mp4 with the new window size
        if hasattr(self, "current_gif") and self.current_gif:
            current_frame = (
                self.current_frame_index if hasattr(self, "current_frame_index") else 0
            )
            self.load_gif(self.current_gif.filename)
            # Show the same frame index after resizing
            if self.frames:
                self.label.config(
                    image=self.frames[min(current_frame, len(self.frames) - 1)]
                )
        elif hasattr(self, "video_path") and self.video_path:
            current_frame = (
                self.current_frame_index if hasattr(self, "current_frame_index") else 0
            )
            self.load_mp4(self.video_path)
            if self.frames:
                self.label.config(
                    image=self.frames[min(current_frame, len(self.frames) - 1)]
                )

    def start(self):
        self.root.after(0, self.play_gifs)
        self.root.protocol("WM_DELETE_WINDOW", self.stop)
        self.root.mainloop()

    def stop(self):
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
    folder_path = (
        r"mygifs"  # Replace with the path to your folder containing media files
    )
    interval = 60  # Time in seconds before switching to the next media
    player = GifsFrame(folder_path, interval)
    player.start()

# 12 12 24
