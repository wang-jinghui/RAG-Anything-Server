"""
Remote MinerU API Parser

Two flows supported:
  A) Local file  → POST /api/v4/file-urls/batch (get upload URL)
                 → PUT <upload_url> (upload file)
                 → GET /api/v4/extract-results/batch/{batch_id} (poll)
                 → download zip → parse content_list.json

  B) Remote URL  → POST /api/v4/extract/task (submit)
                 → GET /api/v4/extract/task/{task_id} (poll)
                 → download zip → parse content_list.json
"""

import os
import io
import json
import asyncio
import zipfile
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiohttp
from dotenv import load_dotenv

from raganything.parser import Parser

load_dotenv()

logger = logging.getLogger(__name__)


class MineruExecutionError(Exception):
    def __init__(self, status: int, msg: str):
        self.return_code = status
        self.error_msg = msg
        super().__init__(f"MinerU API error {status}: {msg}")


class RemoteMineruParser(Parser):
    """
    Remote MinerU Precision Extract API parser.

    Supports local file upload via /api/v4/file-urls/batch (PUT signed URL flow)
    and remote URL submission via /api/v4/extract/task.
    """

    def __init__(
        self,
        api_base_url: Optional[str] = None,
        api_token: Optional[str] = None,
        model_version: Optional[str] = None,
        timeout: int = 300,
        poll_interval: float = 3.0,
    ):
        super().__init__()
        self.api_base_url = (api_base_url or os.getenv("MINERU_API_BASE_URL", "https://mineru.net")).rstrip("/")
        self.api_token = api_token or os.getenv("MINERU_API_TOKEN")
        self.model_version = model_version or os.getenv("MINERU_MODEL_VERSION", "vlm")
        self.timeout = timeout
        self.poll_interval = poll_interval
        self._session: Optional[aiohttp.ClientSession] = None

        if not self.api_token:
            raise ValueError("MINERU_API_TOKEN must be set in environment or passed as parameter")

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.api_token}"},
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    # ------------------------------------------------------------------
    # Flow A: local file upload
    # ------------------------------------------------------------------

    async def _get_upload_url(self, file_name: str) -> tuple[str, str]:
        """
        POST /api/v4/file-urls/batch
        Returns (batch_id, upload_url)
        """
        session = await self._get_session()
        url = f"{self.api_base_url}/api/v4/file-urls/batch"
        payload = {
            "files": [{"name": file_name}],
            "model_version": self.model_version,
            "enable_formula": True,
            "enable_table": True,
        }
        async with session.post(url, json=payload) as resp:
            body = await resp.json()
            if resp.status != 200 or body.get("code") != 0:
                raise MineruExecutionError(resp.status, f"get_upload_url failed: {body}")
            data = body["data"]
            return data["batch_id"], data["file_urls"][0]

    async def _upload_file(self, upload_url: str, file_path: Path) -> None:
        """PUT file bytes to the pre-signed OSS URL.
        
        OSS pre-signed URLs require exact Content-Length and no chunked encoding.
        Use requests (sync) via asyncio.to_thread to avoid aiohttp chunked transfer.
        """
        import requests as _requests
        
        def _do_put():
            with open(file_path, "rb") as f:
                data = f.read()
            resp = _requests.put(upload_url, data=data, timeout=self.timeout)
            return resp.status_code, resp.text[:200]
        
        status, text = await asyncio.to_thread(_do_put)
        if status not in (200, 201):
            raise MineruExecutionError(status, f"file upload failed: {text}")

    async def _poll_batch(self, batch_id: str) -> str:
        """
        GET /api/v4/extract-results/batch/{batch_id}
        Polls until state=done, returns full_zip_url.
        """
        session = await self._get_session()
        url = f"{self.api_base_url}/api/v4/extract-results/batch/{batch_id}"
        elapsed = 0
        while elapsed < self.timeout:
            async with session.get(url) as resp:
                body = await resp.json()
                if resp.status != 200 or body.get("code") != 0:
                    raise MineruExecutionError(resp.status, f"poll_batch failed: {body}")
                results = body["data"].get("extract_result", [])
                if not results:
                    await asyncio.sleep(self.poll_interval)
                    elapsed += self.poll_interval
                    continue
                item = results[0]
                state = item.get("state", "")
                logger.debug(f"[MinerU] batch {batch_id} state={state}")
                if state == "done":
                    return item["full_zip_url"]
                if state == "failed":
                    raise MineruExecutionError(0, f"task failed: {item.get('err_msg', '')}")
            await asyncio.sleep(self.poll_interval)
            elapsed += self.poll_interval
        raise TimeoutError(f"MinerU batch {batch_id} timed out after {self.timeout}s")

    # ------------------------------------------------------------------
    # Flow B: remote URL submission
    # ------------------------------------------------------------------

    async def _submit_url_task(self, file_url: str) -> str:
        """
        POST /api/v4/extract/task
        Returns task_id.
        """
        session = await self._get_session()
        url = f"{self.api_base_url}/api/v4/extract/task"
        payload = {
            "url": file_url,
            "model_version": self.model_version,
            "enable_formula": True,
            "enable_table": True,
        }
        async with session.post(url, json=payload) as resp:
            body = await resp.json()
            if resp.status != 200 or body.get("code") != 0:
                raise MineruExecutionError(resp.status, f"submit_url_task failed: {body}")
            return body["data"]["task_id"]

    async def _poll_task(self, task_id: str) -> str:
        """
        GET /api/v4/extract/task/{task_id}
        Polls until state=done, returns full_zip_url.
        """
        session = await self._get_session()
        url = f"{self.api_base_url}/api/v4/extract/task/{task_id}"
        elapsed = 0
        while elapsed < self.timeout:
            async with session.get(url) as resp:
                body = await resp.json()
                if resp.status != 200 or body.get("code") != 0:
                    raise MineruExecutionError(resp.status, f"poll_task failed: {body}")
                data = body["data"]
                state = data.get("state", "")
                logger.debug(f"[MinerU] task {task_id} state={state}")
                if state == "done":
                    return data["full_zip_url"]
                if state == "failed":
                    raise MineruExecutionError(0, f"task failed: {data.get('err_msg', '')}")
            await asyncio.sleep(self.poll_interval)
            elapsed += self.poll_interval
        raise TimeoutError(f"MinerU task {task_id} timed out after {self.timeout}s")

    # ------------------------------------------------------------------
    # Download & parse result zip
    # ------------------------------------------------------------------

    async def _download_and_parse(self, zip_url: str) -> List[Dict[str, Any]]:
        """Download result zip and extract content_list from it."""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as s:
            async with s.get(zip_url) as resp:
                if resp.status != 200:
                    raise MineruExecutionError(resp.status, f"zip download failed: {zip_url}")
                zip_bytes = await resp.read()

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            logger.debug(f"[MinerU] zip contents: {names}")

            # Prefer content_list.json (structured blocks)
            content_list_file = next(
                (n for n in names if n.endswith("content_list.json") and "v2" not in n),
                next((n for n in names if "content_list" in n), None)
            )
            # Fallback to full.md
            md_file = next((n for n in names if n.endswith("full.md")), None)

            if content_list_file:
                raw = json.loads(zf.read(content_list_file).decode("utf-8"))
                return self._normalize_content_list(raw)
            elif md_file:
                md_text = zf.read(md_file).decode("utf-8")
                return [{"type": "text", "text": md_text, "page_idx": 0}]
            else:
                raise ValueError(f"No usable content found in zip. Files: {names}")

    def _normalize_content_list(self, raw: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize MinerU content_list.json blocks to RAGAnything format."""
        result = []
        for block in raw:
            t = block.get("type", "text")
            item: Dict[str, Any] = {"type": t, "page_idx": block.get("page_idx", 0)}
            if t == "text":
                item["text"] = block.get("text", "")
            elif t == "image":
                item["img_path"] = block.get("img_path", "")
                item["image_caption"] = block.get("img_caption", [])
            elif t == "table":
                item["table_body"] = block.get("table_body", "")
                item["table_caption"] = block.get("table_caption", [])
            elif t == "equation":
                item["latex"] = block.get("latex", "")
                item["text"] = block.get("text", "")
            else:
                item["text"] = block.get("text", str(block))
            result.append(item)
        return result

    # ------------------------------------------------------------------
    # Public parse methods (sync — called by RAGAnything via asyncio.to_thread)
    # ------------------------------------------------------------------

    def parse_pdf(
        self,
        pdf_path: Union[str, Path],
        output_dir: Optional[str] = None,
        method: str = "auto",
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Sync entry point — wraps the async implementation for asyncio.to_thread compatibility."""
        return asyncio.run(self._parse_pdf_async(Path(pdf_path), **kwargs))

    async def _parse_pdf_async(self, pdf_path: Path, **kwargs) -> List[Dict[str, Any]]:
        """Parse a local file via MinerU remote API (async implementation)."""
        if not pdf_path.exists():
            raise FileNotFoundError(f"File not found: {pdf_path}")

        logger.info(f"[MinerU] Uploading {pdf_path.name} ({pdf_path.stat().st_size // 1024}KB)...")

        batch_id, upload_url = await self._get_upload_url(pdf_path.name)
        logger.info(f"[MinerU] batch_id={batch_id}, uploading to OSS...")

        await self._upload_file(upload_url, pdf_path)
        logger.info("[MinerU] Upload complete, waiting for extraction...")

        zip_url = await self._poll_batch(batch_id)
        logger.info(f"[MinerU] Extraction done, downloading result zip...")

        content_list = await self._download_and_parse(zip_url)
        logger.info(f"[MinerU] Parsed {len(content_list)} content blocks")
        return content_list

    async def parse_url(self, file_url: str) -> List[Dict[str, Any]]:
        """Parse a remote file URL via MinerU API (async, call directly with await)."""
        logger.info(f"[MinerU] Submitting URL task: {file_url}")
        task_id = await self._submit_url_task(file_url)
        logger.info(f"[MinerU] task_id={task_id}, polling...")
        zip_url = await self._poll_task(task_id)
        content_list = await self._download_and_parse(zip_url)
        logger.info(f"[MinerU] Parsed {len(content_list)} content blocks")
        return content_list

    def parse_image(self, image_path, output_dir=None, lang=None, **kwargs):
        return self.parse_pdf(image_path, output_dir, method="ocr", lang=lang, **kwargs)

    def parse_document(self, file_path, method="auto", output_dir=None, lang=None, **kwargs):
        return self.parse_pdf(file_path, output_dir, method=method, lang=lang, **kwargs)

    def check_installation(self) -> bool:
        """Always True — remote API, no local install needed."""
        return bool(self.api_token)
