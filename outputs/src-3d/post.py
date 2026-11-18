"""Post-process the three.js frames: vignette, grain, titles, subtitles, letterbox, fades, encode."""
import os, sys, subprocess
from PIL import Image, ImageDraw, ImageChops, ImageEnhance
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/tmp/claude-0/-home-user-free-claude-code/758068d0-026b-523b-bc43-fb5e21c41fd6/scratchpad/anime")
from make_anime import SUBS, grain, VIG, smooth, clamp, font, W, H, FPS, N, DUR

FRAMES = os.path.join(HERE, "frames")
OUT = os.path.join(HERE, "out")
AUDIO = "/tmp/claude-0/-home-user-free-claude-code/758068d0-026b-523b-bc43-fb5e21c41fd6/scratchpad/anime/out/audio.wav"
os.makedirs(OUT, exist_ok=True)

def text_outlined(img, s, xy, size, col, a, bold=True):
    """Text with a dark outline so it reads over bright city lights."""
    if a <= 0.01:
        return
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).text(xy, s, font=font(size, bold), fill=int(255 * clamp(a)), anchor="mm",
                           stroke_width=max(2, size // 22), stroke_fill=int(255 * clamp(a)))
    ImageDraw.Draw(m).text(xy, s, font=font(size, bold), fill=int(255 * clamp(a)), anchor="mm")
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    img.paste(dark, (0, 0), m.point(lambda v: int(v * 0.85)))
    img.paste(Image.new("RGB", (W, H), col), (0, 0), m)

def overlays(img, t):
    if t < 18:
        a = smooth((t - 4) / 2) * (1 - smooth((t - 14) / 2))
        text_outlined(img, "CRIMSON DAWN", (W / 2, 200), 104, (255, 150, 170), a)
        text_outlined(img, "Capítulo I · La ciudad bajo la lluvia", (W / 2, 290), 30, (235, 220, 245),
                      smooth((t - 5) / 2) * (1 - smooth((t - 14) / 2)), bold=False)
    if t >= 105:
        text_outlined(img, "CRIMSON DAWN", (W / 2, 250), 110, (255, 215, 135), smooth((t - 105) / 3))
        text_outlined(img, "Amanecer Carmesí", (W / 2, 350), 42, (255, 175, 150), smooth((t - 107) / 3), bold=False)
        text_outlined(img, "Animación 3D · 2 minutos", (W / 2, 420), 26, (210, 200, 225),
                      smooth((t - 109) / 3), bold=False)

def subtitles(img, t):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 80], fill=(0, 0, 0))
    d.rectangle([0, H - 80, W, H], fill=(0, 0, 0))
    for a, b, s in SUBS:
        al = smooth((t - a) / 0.6) * smooth((b - t) / 0.6)
        if al > 0.01:
            from make_anime import text_alpha
            text_alpha(img, s, (W / 2, H - 40), 30, (255, 240, 225), al, bold=False)

def frame_image(i):
    t = i / FPS
    img = Image.open(os.path.join(FRAMES, f"f_{i:05d}.png")).convert("RGB")
    img = ImageChops.multiply(img, VIG)
    img = grain(img, i)
    overlays(img, t)
    subtitles(img, t)
    fade = min(1.0, t / 1.0, (DUR - t) / 1.5)
    if fade < 1:
        img = ImageEnhance.Brightness(img).enhance(max(0.0, fade))
    return img

if __name__ == "__main__":
    video = os.path.join(OUT, "video_only_3d.mp4")
    final = os.path.join(OUT, "crimson_dawn_3d_2min.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                           "-preset", "medium", "-crf", "27", "-tune", "grain", "-pix_fmt", "yuv420p", video],
                          stdin=subprocess.PIPE)
    for i in range(N):
        ff.stdin.write(frame_image(i).tobytes())
        if i % 480 == 0:
            print("post", i, "/", N, flush=True)
    ff.stdin.close(); ff.wait()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", AUDIO, "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", final], check=True)
    print("done", final, flush=True)
