import os
import random
import tkinter as tk
from PIL import Image, ImageTk
import time
from cv2 import VideoCapture, cvtColor, COLOR_BGR2RGB, resize, CAP_PROP_FPS
import json


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
        self.root.title("Random Media Player")
        self.root.geometry("250x250")  # Set initial window size
        self.root.attributes("-topmost", True)  # Always stay on top
        self.root.resizable(True, True)  # Disable window resizing
        self.label = tk.Label(self.root)
        self.label.pack(fill=tk.BOTH, expand=True)
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

    def load_gif(self, gif_path):
        self.current_gif = Image.open(gif_path)
        self.frames = []
        self.durations = []  # Store frame durations
        width, height = 200, 200  # Fixed size
        try:
            while True:
                frame = self.current_gif.copy()
                # Make frame square by padding with yellow if needed
                orig_w, orig_h = frame.size
                if orig_w != orig_h:
                    side = max(orig_w, orig_h)
                    # Nice yellow RGBA: (255, 221, 51, 255)
                    new_frame = Image.new("RGBA", (side, side), (255, 221, 51, 255))
                    new_frame.paste(frame, ((side - orig_w) // 2, (side - orig_h) // 2))
                    frame = new_frame
                frame = frame.resize((width, height), Image.LANCZOS)
                frame = ImageTk.PhotoImage(frame)
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
        width, height = 200, 200  # Fixed size
        while True:
            ret, frame = self.video_capture.read()
            if not ret:
                break
            frame = cvtColor(frame, COLOR_BGR2RGB)
            # Make frame square by padding with yellow if needed
            orig_h, orig_w, _ = frame.shape
            if orig_w != orig_h:
                side = max(orig_w, orig_h)
                import numpy as np

                # Nice yellow RGB: (255, 221, 51)
                square_frame = np.ones((side, side, 3), dtype=frame.dtype) * np.array(
                    [255, 221, 51], dtype=frame.dtype
                )
                y_offset = (side - orig_h) // 2
                x_offset = (side - orig_w) // 2
                square_frame[
                    y_offset : y_offset + orig_h, x_offset : x_offset + orig_w, :
                ] = frame
                frame = square_frame
            frame = resize(frame, (width, height))  # Resize frame to fit window
            frame = ImageTk.PhotoImage(Image.fromarray(frame))
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
                self.root.after(
                    self.interval * 1000, update_media
                )  # Schedule next update

        self.root.after(self.interval * 1000, update_media)  # Initial scheduling

        while True:
            for frame, duration in zip(self.frames, self.durations):
                if not self.running:
                    break
                self.label.config(image=frame)
                self.root.update()
                time.sleep(duration)  # Use the frame-specific duration

    def start(self):
        self.root.after(0, self.play_gifs)
        self.root.protocol("WM_DELETE_WINDOW", self.stop)
        self.root.mainloop()

    def stop(self):
        self.running = False
        self.root.destroy()

    def reload_current_media(self):
        # Reload the current gif or mp4 with the new window size
        if hasattr(self, "current_gif") and self.current_gif:
            self.load_gif(self.current_gif.filename)
        elif hasattr(self, "video_path") and self.video_path:
            self.load_mp4(self.video_path)


if __name__ == "__main__":
    folder_path = (
        r"mygifs"  # Replace with the path to your folder containing media files
    )
    interval = 30  # Time in seconds before switching to the next media
    player = GifsFrame(folder_path, interval)
    player.start()

# 12 12 24
