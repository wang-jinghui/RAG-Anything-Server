"""
Local MinerU API Parser

Parser that integrates with a locally deployed MinerU HTTP API service.
Converts relative image paths to absolute paths for RAGAnything compatibility.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiohttp
from dotenv import load_dotenv

from raganything.parser import Parser

load_dotenv()


class LocalMineruAPIParser(Parser):
    """
    Parser for local MinerU HTTP API service.
    
    This parser sends documents to a locally deployed MinerU API,
    receives the parsing results, and converts relative image paths
    to absolute paths for RAGAnything compatibility.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        output_base_dir: Optional[str] = None,
        timeout: int = 300,
    ):
        """
        Initialize Local MinerU API Parser.
        
        Args:
            api_url: Base URL of the MinerU API service (default: from env MINERU_LOCAL_API_URL)
            output_base_dir: Base directory for storing parsed outputs (default: from env MINERU_OUTPUT_DIR or ./mineru_output)
            timeout: Request timeout in seconds (default: 300)
        """
        super().__init__()
        
        # API configuration
        self.api_url = api_url or os.getenv("MINERU_LOCAL_API_URL", "http://localhost:8001")
        self.api_url = self.api_url.rstrip("/")
        
        # Output directory configuration
        self.output_base_dir = Path(output_base_dir or os.getenv("MINERU_OUTPUT_DIR", "./mineru_output"))
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Timeout
        self.timeout = timeout
        
        self.logger.info(f"Local MinerU API Parser initialized:")
        self.logger.info(f"  API URL: {self.api_url}")
        self.logger.info(f"  Output base dir: {self.output_base_dir.resolve()}")

    async def _call_api(
        self,
        file_path: Path,
        backend: str = "hybrid-auto-engine",
        parse_method: str = "auto",
        lang_list: List[str] = ["ch"],
        return_md: bool = True,
        return_content_list: bool = True,
        return_images: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call the local MinerU API to parse a document.
        
        Args:
            file_path: Path to the document file
            backend: Parsing backend
            parse_method: Parse method (auto/txt/ocr)
            lang_list: Language list
            return_md: Whether to return markdown
            return_content_list: Whether to return content list
            return_images: Whether to return images
            **kwargs: Additional parameters
            
        Returns:
            Parsed result dictionary
        """
        # Prepare form data
        data = aiohttp.FormData()
        data.add_field('files', open(file_path, 'rb'), filename=file_path.name, content_type='application/pdf')
        data.add_field('output_dir', str(self.output_base_dir))
        data.add_field('backend', backend)
        data.add_field('parse_method', parse_method)
        
        # Add language list as individual items
        for lang in lang_list:
            data.add_field('lang_list', lang)
        
        # Add boolean flags
        data.add_field('formula_enable', 'true')
        data.add_field('table_enable', 'true')
        data.add_field('return_md', str(return_md).lower())
        data.add_field('return_content_list', str(return_content_list).lower())
        data.add_field('return_images', str(return_images).lower())
        data.add_field('return_middle_json', 'false')
        data.add_field('return_model_output', 'false')
        data.add_field('response_format_zip', 'false')
        data.add_field('start_page_id', '0')
        data.add_field('end_page_id', '99999')
        
        # Make API request
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/file_parse",
                data=data,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"MinerU API error ({resp.status}): {error_text}")
                
                result = await resp.json()
                return result

    def _extract_file_result(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract the file-specific result from API response.
        
        The API returns: {"backend": ..., "version": ..., "results": {"filename": {...}}}
        We need to extract the inner result for the specific file.
        
        Args:
            api_response: Raw API response
            
        Returns:
            File-specific result dictionary
        """
        if 'results' not in api_response:
            raise ValueError("API response missing 'results' field")
        
        results = api_response['results']
        
        # Results is a dict with filename keys
        if isinstance(results, dict):
            # Get the first (and usually only) file result
            for filename, file_result in results.items():
                self.logger.debug(f"Extracted result for file: {filename}")
                return file_result
        
        raise ValueError(f"Unexpected results format: {type(results)}")

    def _convert_relative_paths_to_absolute(
        self, 
        content_list: List[Any], 
        output_dir: Path,
        images_data: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Convert relative image paths in content_list to absolute paths.
        
        Also handles the case where content_list is returned as a character array
        that needs to be reconstructed into JSON.
        
        If images_data is provided (base64 encoded images), saves ALL of them to disk,
        regardless of whether they are referenced in content_list.
        This ensures formula renderings, table images, and other auxiliary images are preserved.
        
        Args:
            content_list: Content list from API (may be char array or parsed list)
            output_dir: Output directory for resolving relative paths
            images_data: Optional dict mapping filename to base64 image data
            
        Returns:
            Content list with absolute image paths
        """
        # Check if content_list is a character array that needs reconstruction
        if content_list and all(isinstance(item, str) and len(item) <= 2 for item in content_list[:10]):
            self.logger.info("Reconstructing content_list from character array")
            full_string = ''.join(content_list)
            try:
                content_list = json.loads(full_string)
                self.logger.info(f"Successfully parsed {len(content_list)} content blocks")
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse content_list JSON: {e}")
                return []
        
        # Create images subdirectory
        images_dir = output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Collect all image filenames referenced in content_list
        referenced_images = set()
        for item in content_list:
            if isinstance(item, dict):
                for field_name in ["img_path", "table_img_path", "equation_img_path"]:
                    if field_name in item and item[field_name]:
                        img_filename = Path(item[field_name]).name
                        referenced_images.add(img_filename)
        
        self.logger.info(f"Found {len(referenced_images)} referenced images in content_list")
        
        # Step 2: Save ONLY referenced images from images_data
        if images_data and isinstance(images_data, dict):
            saved_count = 0
            skipped_count = 0
            
            for img_filename, base64_data in images_data.items():
                # Only save if this image is referenced in content_list
                if img_filename not in referenced_images:
                    self.logger.debug(f"Skipping unreferenced image: {img_filename}")
                    skipped_count += 1
                    continue
                
                try:
                    # Extract actual base64 data (remove data:image/xxx;base64, prefix)
                    if ',' in base64_data:
                        base64_data = base64_data.split(',', 1)[1]
                    
                    # Decode and save
                    import base64
                    image_bytes = base64.b64decode(base64_data)
                    image_path = images_dir / img_filename
                    
                    with open(image_path, 'wb') as f:
                        f.write(image_bytes)
                    
                    saved_count += 1
                    self.logger.debug(f"Saved referenced image: {img_filename} ({len(image_bytes)} bytes)")
                    
                except Exception as e:
                    self.logger.error(f"Failed to save image {img_filename}: {e}")
            
            self.logger.info(f"Saved {saved_count} images, skipped {skipped_count} unreferenced images")
        
        # Step 3: Convert relative paths in content_list to absolute paths
        resolved_content_list = []
        for item in content_list:
            if isinstance(item, dict):
                # Handle all image path fields (same as MineruParser)
                for field_name in ["img_path", "table_img_path", "equation_img_path"]:
                    if field_name in item and item[field_name]:
                        img_path_str = item[field_name]
                        img_filename = Path(img_path_str).name
                        
                        # The image should already be saved in Step 1
                        # Just convert the path to absolute
                        img_path_obj = Path(img_path_str)
                        if not img_path_obj.is_absolute():
                            absolute_path = (images_dir / img_filename).resolve()
                            
                            # Security check (same as MineruParser)
                            resolved_base = images_dir.resolve()
                            if not absolute_path.is_relative_to(resolved_base):
                                self.logger.warning(
                                    f"Potential path traversal detected in {field_name}: {item[field_name]}. Skipping."
                                )
                                item[field_name] = ""  # Clear unsafe path
                                continue
                            
                            item[field_name] = str(absolute_path)
                            self.logger.debug(f"Converted {field_name}: {img_filename} -> {absolute_path}")
                
                resolved_content_list.append(item)
            else:
                # Keep non-dict items as-is (shouldn't happen after reconstruction)
                resolved_content_list.append(item)
        
        return resolved_content_list

    def parse_pdf(
        self,
        pdf_path: Union[str, Path],
        output_dir: Optional[str] = None,
        method: str = "auto",
        lang: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Parse PDF using local MinerU API.
        
        This is the synchronous entry point called by RAGAnything via asyncio.to_thread.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Output directory (used for image path resolution)
            method: Parse method (auto/txt/ocr)
            lang: Language code
            **kwargs: Additional parameters
            
        Returns:
            List of content block dictionaries
        """
        pdf_path = Path(pdf_path).resolve()
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Determine output directory for this file
        if output_dir:
            file_output_dir = Path(output_dir)
        else:
            # Use a subdirectory based on filename hash (similar to unique_output_dir)
            import hashlib
            path_hash = hashlib.md5(str(pdf_path).encode()).hexdigest()[:8]
            file_output_dir = self.output_base_dir / f"{pdf_path.stem}_{path_hash}"
        
        file_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare language list
        lang_list = [lang] if lang else ["ch"]
        
        # Call API asynchronously
        try:
            # Always enable return_images to get base64 image data (same as MinerU CLI saves images)
            api_response = asyncio.run(self._call_api(
                file_path=pdf_path,
                backend=kwargs.get('backend', 'hybrid-auto-engine'),
                parse_method=method,
                lang_list=lang_list,
                return_md=True,
                return_content_list=True,
                return_images=True,  # Always enable to simulate MinerU CLI behavior
                **kwargs
            ))
            
            # Extract file-specific result
            file_result = self._extract_file_result(api_response)
            
            # Get content list and images data
            content_list = file_result.get('content_list', [])
            images_data = file_result.get('images', None)
            
            self.logger.info(f"Content list length: {len(content_list) if isinstance(content_list, list) else 'N/A'}")
            self.logger.info(f"Images data type: {type(images_data)}")
            if isinstance(images_data, dict):
                self.logger.info(f"Images data keys: {list(images_data.keys())}")
            
            # Convert relative paths to absolute (and save base64 images if present)
            if content_list:
                content_list = self._convert_relative_paths_to_absolute(
                    content_list, 
                    file_output_dir,
                    images_data=images_data
                )
            
            self.logger.info(f"Parsed {len(content_list)} content blocks from {pdf_path.name}")
            return content_list
            
        except Exception as e:
            self.logger.error(f"Failed to parse PDF via local API: {e}")
            raise

    def parse_image(
        self,
        image_path: Union[str, Path],
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Parse image using local MinerU API.
        
        Args:
            image_path: Path to the image file
            output_dir: Output directory
            lang: Language code
            **kwargs: Additional parameters
            
        Returns:
            List of content block dictionaries
        """
        # Treat image as PDF for parsing (MinerU supports image files)
        return self.parse_pdf(image_path, output_dir, method="ocr", lang=lang, **kwargs)

    def parse_document(
        self,
        file_path: Union[str, Path],
        method: str = "auto",
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Generic document parsing entry point.
        
        Args:
            file_path: Path to the document
            method: Parse method
            output_dir: Output directory
            lang: Language code
            **kwargs: Additional parameters
            
        Returns:
            List of content block dictionaries
        """
        return self.parse_pdf(file_path, output_dir, method=method, lang=lang, **kwargs)

    def check_installation(self) -> bool:
        """
        Check if the local MinerU API service is accessible.
        
        Returns:
            True if API is reachable, False otherwise
        """
        try:
            import requests
            resp = requests.get(f"{self.api_url}/openapi.json", timeout=5)
            return resp.status_code == 200
        except Exception as e:
            self.logger.warning(f"Cannot connect to MinerU API at {self.api_url}: {e}")
            return False
