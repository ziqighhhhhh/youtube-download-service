import asyncio
import shutil
from pathlib import Path
from typing import Optional, AsyncGenerator, Callable
from config import DATA_DIR


class YtDlpManager:
    def __init__(self):
        self.output_dir = DATA_DIR / "temp"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.killed = False

    async def get_video_count(self, url: str) -> int:
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--simulate",
            "--flat-playlist",
            "--print",
            "%(n_entries)s",
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        try:
            return max(int(stdout.decode().strip()), 1)
        except:
            return 1

    async def download_stream(
        self, url: str, cookies_file: str, callback: Optional[Callable] = None
    ) -> AsyncGenerator[str, None]:
        import tempfile

        tmp = Path(tempfile.mkdtemp(dir=self.output_dir))
        cmd = [
            "yt-dlp",
            "--cookies",
            cookies_file,
            "--extractor-args",
            "youtube:player_client=web",
            "--sleep-requests",
            "3",
            "--min-sleep-interval",
            "3",
            "--max-sleep-interval",
            "10",
            "--ignore-errors",
            "--no-overwrites",
            "--concurrent-fragments",
            "2",
            "--retries",
            "10",
            "--fragment-retries",
            "10",
            "--merge-output-format",
            "mp4",
            "-f",
            "best[ext=mp4]/best",
            "--newline",
            "--progress",
            "-o",
            str(tmp / "%(upload_date)s_%(title).100s [%(id)s].%(ext)s"),
            url,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        ok, fail = 0, 0
        try:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="ignore").strip()
                if text:
                    yield text
                    if callback:
                        await callback(text)
                    if "ERROR" in text:
                        fail += 1
                    elif (
                        "100%" in text
                        or "already been downloaded" in text.lower()
                    ):
                        ok += 1
                if self.killed:
                    proc.kill()
                    break
            await proc.wait()
        except Exception as e:
            if proc.returncode is None:
                proc.kill()
            yield f"ERROR: {e}"
        if tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)
        yield f"__DONE__:{ok}:{fail}"

    def kill(self):
        self.killed = True
