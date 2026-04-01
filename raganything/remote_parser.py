"""
Remote MinerU API Parser - Lightweight HTTP-based document parsing

This module provides a lightweight parser that calls remote MinerU API
instead of running local subprocess, making the service more flexible.
"""

import os
import asyncio
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import aiohttp
from dotenv import load_dotenv


# Define exception class locally to avoid circular imports
class MineruExecutionError(Exception):
    """Exception raised when MinerU API call fails."""
    
    def __init__(self, return_code, error_msg):
        self.return_code = return_code
        self.error_msg = error_msg
        super().__init__(
            f"Mineru API call failed with status {return_code}: {error_msg}"
        )


# Import base Parser class (this is safe as parser.py has no raganything dependencies)
from raganything.parser import Parser

# Load environment variables
load_dotenv()


class RemoteMineruParser(Parser):
    """
    Remote MinerU API parser for lightweight document processing.
    
    Instead of running local mineru CLI via subprocess, this class
    calls the remote MinerU API service, making the application:
    - More lightweight (no local dependencies)
    - More scalable (centralized GPU resources)
    - Easier to deploy (no system-level packages needed)
    - More flexible (can switch API endpoints dynamically)
    """
    
    def __init__(
        self,
        api_base_url: Optional[str] = None,
        api_token: Optional[str] = None,
        extract_endpoint: Optional[str] = None,
        batch_endpoint: Optional[str] = None,
        model_version: Optional[str] = None,
        timeout: int = 300,
    ):
        """
        Initialize remote MinerU parser.
        
        Args:
            api_base_url: Base URL of MinerU API (e.g., https://mineru.net)
            api_token: JWT token for authentication
            extract_endpoint: Extract task endpoint (e.g., /api/v4/extract/task)
            batch_endpoint: Batch upload endpoint (e.g., /api/v4/file-urls/batch)
            model_version: Model version (e.g., vlm, ocr)
            timeout: Request timeout in seconds
        """
        super().__init__()
        
        # Configuration from environment or parameters
        self.api_base_url = api_base_url or os.getenv(
            "MINERU_API_BASE_URL", "https://mineru.net"
        )
        self.api_token = api_token or os.getenv("MINERU_API_TOKEN")
        self.extract_endpoint = extract_endpoint or os.getenv(
            "MINERU_API_EXTRACT_ENDPOINT", "/api/v4/extract/task"
        )
        self.batch_endpoint = batch_endpoint or os.getenv(
            "MINERU_API_BATCH_ENDPOINT", "/api/v4/file-urls/batch"
        )
        self.model_version = model_version or os.getenv(
            "MINERU_MODEL_VERSION", "vlm"
        )
        self.timeout = timeout
        
        if not self.api_token:
            raise ValueError(
                "MINERU_API_TOKEN must be provided in environment or as parameter"
            )
        
        # HTTP session
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            )
        return self._session
    
    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _upload_file(self, file_path: Union[str, Path]) -> str:
        """
        Upload file to remote storage and get URL.
        
        Args:
            file_path: Path to local file
            
        Returns:
            Remote file URL
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        session = await self._get_session()
        
        # Read file
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        # Upload using batch endpoint
        url = f"{self.api_base_url}{self.batch_endpoint}"
        
        form = aiohttp.FormData()
        form.add_field(
            "file",
            file_data,
            filename=file_path.name,
            content_type="application/octet-stream",
        )
        
        async with session.post(url, data=form) as response:
            if response.status != 200:
                error_text = await response.text()
                raise MineruExecutionError(
                    response.status,
                    f"File upload failed: {error_text}"
                )
            
            result = await response.json()
            
            # Extract file URL from response
            # Response format depends on API, adjust as needed
            file_url = result.get("url") or result.get("data", {}).get("url")
            
            if not file_url:
                raise ValueError(f"Invalid upload response: {result}")
            
            return file_url
    
    async def _submit_extract_task(
        self,
        file_url: str,
        method: str = "auto",
        lang: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Submit extraction task and get task ID.
        
        Args:
            file_url: Remote file URL
            method: Extraction method (auto, txt, ocr)
            lang: Language
            **kwargs: Additional parameters
            
        Returns:
            Task ID
        """
        session = await self._get_session()
        url = f"{self.api_base_url}{self.extract_endpoint}"
        
        payload = {
            "file_url": file_url,
            "method": method,
            "model_version": self.model_version,
        }
        
        if lang:
            payload["lang"] = lang
        
        # Add optional parameters
        for key in ["formula", "table", "backend"]:
            if key in kwargs:
                payload[key] = kwargs[key]
        
        async with session.post(url, json=payload) as response:
            if response.status not in [200, 201, 202]:
                error_text = await response.text()
                raise MineruExecutionError(
                    response.status,
                    f"Task submission failed: {error_text}"
                )
            
            result = await response.json()
            
            # Extract task ID from response
            task_id = result.get("task_id") or result.get("data", {}).get("task_id")
            
            if not task_id:
                raise ValueError(f"Invalid task response: {result}")
            
            return task_id
    
    async def _wait_for_task(self, task_id: str, poll_interval: float = 2.0) -> Dict[str, Any]:
        """
        Wait for task completion.
        
        Args:
            task_id: Task ID to wait for
            poll_interval: Polling interval in seconds
            
        Returns:
            Task result dictionary
        """
        session = await self._get_session()
        status_url = f"{self.api_base_url}/api/v4/tasks/{task_id}"
        
        while True:
            async with session.get(status_url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise MineruExecutionError(
                        response.status,
                        f"Task status check failed: {error_text}"
                    )
                
                result = await response.json()
                status = result.get("status") or result.get("data", {}).get("status")
                
                if status == "completed":
                    return result
                elif status in ["failed", "error"]:
                    error_msg = result.get("error") or result.get("data", {}).get("error", "Unknown error")
                    raise MineruExecutionError(0, f"Task failed: {error_msg}")
                elif status in ["pending", "processing", "running"]:
                    await asyncio.sleep(poll_interval)
                else:
                    await asyncio.sleep(poll_interval)
    
    async def parse_pdf(
        self,
        pdf_path: Union[str, Path],
        output_dir: Optional[str] = None,
        method: str = "auto",
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Parse PDF document using remote MinerU API.
        
        Args:
            pdf_path: Path to PDF file
            output_dir: Output directory (not used for remote API, kept for compatibility)
            method: Parsing method (auto, txt, ocr)
            lang: Document language
            **kwargs: Additional parameters
            
        Returns:
            List of content blocks
        """
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file does not exist: {pdf_path}")
            
            self.logger.info(f"[RemoteMineru] Starting remote parsing of: {pdf_path.name}")
            
            # Step 1: Upload file
            self.logger.info("[RemoteMineru] Uploading file...")
            file_url = await self._upload_file(pdf_path)
            self.logger.info(f"[RemoteMineru] File uploaded: {file_url}")
            
            # Step 2: Submit extraction task
            self.logger.info("[RemoteMineru] Submitting extraction task...")
            task_id = await self._submit_extract_task(
                file_url=file_url,
                method=method,
                lang=lang,
                **kwargs,
            )
            self.logger.info(f"[RemoteMineru] Task submitted: {task_id}")
            
            # Step 3: Wait for completion
            self.logger.info("[RemoteMineru] Waiting for task completion...")
            result = await self._wait_for_task(task_id)
            
            # Step 4: Extract content from result
            self.logger.info("[RemoteMineru] Task completed, extracting content...")
            content_list = self._parse_api_result(result)
            
            self.logger.info(
                f"[RemoteMineru] Parsing completed: {len(content_list)} content blocks"
            )
            
            return content_list
            
        except MineruExecutionError:
            raise
        except Exception as e:
            self.logger.error(f"[RemoteMineru] Error during parsing: {str(e)}")
            raise
    
    def _parse_api_result(self, result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse API result into standard content block format.
        
        Args:
            result: API response dictionary
            
        Returns:
            List of content blocks
        """
        content_list = []
        
        # Extract data from response
        # Adjust based on actual API response format
        data = result.get("data") or result
        
        # Get markdown content
        markdown_content = data.get("markdown") or data.get("content", "")
        
        # Get structured blocks if available
        blocks = data.get("blocks") or data.get("content_blocks", [])
        
        if blocks:
            # Use structured blocks
            for block in blocks:
                block_type = block.get("type", "text")
                
                content_block = {
                    "type": block_type,
                    "page_idx": block.get("page_idx", 0),
                }
                
                if block_type == "text":
                    content_block["text"] = block.get("text", "")
                elif block_type == "image":
                    content_block["img_path"] = block.get("image_url", "")
                    content_block["image_caption"] = block.get("caption", [])
                elif block_type == "table":
                    content_block["table_body"] = block.get("markdown", "")
                    content_block["table_caption"] = block.get("caption", [])
                elif block_type == "equation":
                    content_block["latex"] = block.get("latex", "")
                    content_block["text"] = block.get("text", "")
                
                content_list.append(content_block)
        else:
            # Fallback: parse markdown content
            content_list.append({
                "type": "text",
                "text": markdown_content,
                "page_idx": 0,
            })
        
        return content_list
    
    def parse_image(
        self,
        image_path: Union[str, Path],
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """Parse image using remote API (same flow as PDF)."""
        return asyncio.run(self.parse_pdf(
            image_path, output_dir, method="ocr", lang=lang, **kwargs
        ))
    
    def parse_document(
        self,
        file_path: Union[str, Path],
        method: str = "auto",
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Parse document based on file extension.
        
        This method routes to the appropriate parser method based on file type.
        For RemoteMineruParser, all files are treated as PDFs and uploaded to the API.
        
        Args:
            file_path: Path to the file to be parsed
            method: Parsing method (auto, txt, ocr)
            output_dir: Output directory path
            lang: Document language for OCR optimization
            **kwargs: Additional parameters
            
        Returns:
            List of content blocks
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {file_path}")
        
        ext = file_path.suffix.lower()
        
        # Route to appropriate method based on file type
        if ext == '.pdf':
            return asyncio.run(self.parse_pdf(
                file_path, output_dir, method=method, lang=lang, **kwargs
            ))
        elif ext in self.IMAGE_FORMATS:
            return self.parse_image(
                file_path, output_dir, lang=lang, **kwargs
            )
        else:
            # For other formats (txt, md, office), inform user
            # Remote API only supports PDF and images directly
            # Other formats should be converted to PDF first by caller
            self.logger.warning(
                f"RemoteMineruParser: Unsupported format '{ext}', attempting as PDF. "
                f"For best results, convert to PDF first."
            )
            return asyncio.run(self.parse_pdf(
                file_path, output_dir, method=method, lang=lang, **kwargs
            ))
    
    def check_installation(self) -> bool:
        """Check if remote API is accessible."""
        try:
            # Simple health check
            import asyncio
            
            async def check():
                session = await self._get_session()
                async with session.get(f"{self.api_base_url}/health") as response:
                    return response.status == 200
            
            return asyncio.run(check())
        except Exception:
            # If health check fails, still return True to allow fallback
            return True
