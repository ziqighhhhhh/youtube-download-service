import asyncio
import json
import logging
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, AsyncGenerator, Callable
from config import DATA_DIR

logger = logging.getLogger(__name__)


class YtDlpError(RuntimeError):
    pass


class YtDlpManager:
    def __init__(self):
        self.output_dir = DATA_DIR / "temp"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.killed = False

    @staticmethod
    def _count_from_json(stdout: bytes) -> int | None:
        try:
            payload = json.loads(stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        entries = payload.get("entries")
        if isinstance(entries, list):
            return max(len([entry for entry in entries if entry]), 1)
        if payload.get("id"):
            return 1
        return None

    @staticmethod
    @contextmanager
    def _temporary_cookie_file(cookie_text: str | None, parent: Path):
        if not cookie_text:
            yield None
            return
        parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix="cookies-", suffix=".txt", dir=parent)
        path = Path(name)
        try:
            with open(fd, "w", encoding="utf-8", newline="\n") as file:
                file.write(cookie_text)
            yield path
        finally:
            path.unlink(missing_ok=True)

    async def get_video_count(self, url: str, cookie_text: str | None = None) -> int:
        with self._temporary_cookie_file(cookie_text, self.output_dir) as cookie_path:
            cmd = [
                "yt-dlp",
                "--dump-single-json",
                "--flat-playlist",
                "--no-warnings",
                url,
            ]
            if cookie_path:
                cmd[1:1] = ["--cookies", str(cookie_path)]

            proc = await asyncio.to_thread(
                subprocess.run,
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        if proc.returncode != 0:
            message = proc.stderr.decode("utf-8", errors="ignore").strip() or "yt-dlp failed"
            raise YtDlpError(message)

        count = self._count_from_json(proc.stdout)
        if count is None:
            message = proc.stderr.decode("utf-8", errors="ignore").strip() or "Unable to parse yt-dlp output"
            raise YtDlpError(message)
        return count

    async def download_stream(
        self, url: str, cookie_text: str, callback: Optional[Callable] = None
    ) -> AsyncGenerator[str, None]:
        tmp = Path(tempfile.mkdtemp(dir=self.output_dir))
        with self._temporary_cookie_file(cookie_text, self.output_dir) as cookie_path:
            cmd = [
                "yt-dlp",
                "--cookies",
                str(cookie_path),
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
            proc = await asyncio.to_thread(
                subprocess.Popen,
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            ok, fail = 0, 0
            try:
                while True:
                    line = await asyncio.to_thread(proc.stdout.readline)
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
                await asyncio.to_thread(proc.wait)
            except Exception as e:
                if proc.returncode is None:
                    proc.kill()
                logger.exception("yt-dlp download failed")
                yield f"ERROR: {e}"
            finally:
                if tmp.exists():
                    shutil.rmtree(tmp, ignore_errors=True)
            yield f"__DONE__:{ok}:{fail}"

    def kill(self):
        self.killed = True
