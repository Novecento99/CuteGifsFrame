import os
import random
import tkinter as tk
from PIL import Image, ImageTk
import time
from cv2 import VideoCapture, cvtColor, COLOR_BGR2RGB, resize, CAP_PROP_FPS


class GifsFrame:
    def __init__(self, folder_path, interval):
        self.folder_path = folder_path
        self.interval = interval
        self.gif_files = [
            f for f in os.listdir(folder_path) if f.endswith((".gif", ".GIF", ".mp4"))
        ]
        self.current_gif = None
        self.running = True

        # Initialize Tkinter window
        self.root = tk.Tk()
        self.root.title("Random Media Player")
        self.root.geometry("200x200")  # Set initial window size
        self.root.attributes("-topmost", True)  # Always stay on top
        self.root.resizable(False, False)  # Disable window resizing
        self.label = tk.Label(self.root)
        self.label.pack(fill=tk.BOTH, expand=True)
        self.load_random_frames()
        self.display_frames()

    def load_gif(self, gif_path):
        self.current_gif = Image.open(gif_path)
        self.frames = []
        self.durations = []  # Store frame durations
        width, height = 200, 200  # Fixed size
        try:
            while True:
                frame = self.current_gif.copy()
                # Make frame square by padding with white if needed
                orig_w, orig_h = frame.size
                if orig_w != orig_h:
                    side = max(orig_w, orig_h)
                    new_frame = Image.new("RGBA", (side, side), (255, 255, 255, 255))
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
        self.video_capture = VideoCapture(video_path)
        self.video_capture.filename = video_path  # Store for reload
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
            # Make frame square by padding with white if needed
            orig_h, orig_w, _ = frame.shape
            if orig_w != orig_h:
                side = max(orig_w, orig_h)
                import numpy as np

                square_frame = np.ones((side, side, 3), dtype=frame.dtype) * 255
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
        print("Loading random media...")
        print(self.gif_files)
        media_path = os.path.join(self.folder_path, random.choice(self.gif_files))
        print(f"Selected media: {media_path}")
        if media_path.endswith((".gif", ".GIF")):
            self.load_gif(media_path)
        elif media_path.endswith(".mp4"):
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


if __name__ == "__main__":
    folder_path = r"gifs"  # Replace with the path to your folder containing media files
    interval = 5  # Time in seconds before switching to the next media
    player = GifsFrame(folder_path, interval)
    player.start()
