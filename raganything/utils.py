"""
Utility functions for RAGAnything

Contains helper functions for content separation, text insertion, and other utilities
"""

import os
import base64
from typing import Dict, List, Any, Tuple, Optional, Callable
from pathlib import Path
from lightrag.utils import logger


def separate_content(
    content_list: List[Dict[str, Any]],
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Separate text content and multimodal content

    Args:
        content_list: Content list from MinerU parsing

    Returns:
        (text_content, multimodal_items): Pure text content and multimodal items list
    """
    text_parts = []
    multimodal_items = []

    for item in content_list:
        content_type = item.get("type", "text")

        if content_type == "text":
            # Text content
            text = item.get("text", "")
            if text.strip():
                text_parts.append(text)
        else:
            # Multimodal content (image, table, equation, etc.)
            multimodal_items.append(item)

    # Merge all text content
    text_content = "\n\n".join(text_parts)

    logger.info("Content separation complete:")
    logger.info(f"  - Text content length: {len(text_content)} characters")
    logger.info(f"  - Multimodal items count: {len(multimodal_items)}")

    # Count multimodal types
    modal_types = {}
    for item in multimodal_items:
        modal_type = item.get("type", "unknown")
        modal_types[modal_type] = modal_types.get(modal_type, 0) + 1

    if modal_types:
        logger.info(f"  - Multimodal type distribution: {modal_types}")

    return text_content, multimodal_items


def encode_image_to_base64(image_path: str) -> str:
    """
    Encode image file to base64 string

    Args:
        image_path: Path to the image file

    Returns:
        str: Base64 encoded string, empty string if encoding fails
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        return encoded_string
    except Exception as e:
        logger.error(f"Failed to encode image {image_path}: {e}")
        return ""


def validate_image_file(image_path: str, max_size_mb: int = 50) -> bool:
    """
    Validate if a file is a valid image file

    Args:
        image_path: Path to the image file
        max_size_mb: Maximum file size in MB

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        path = Path(image_path)

        logger.debug(f"Validating image path: {image_path}")
        logger.debug(f"Resolved path object: {path}")
        logger.debug(f"Path exists check: {path.exists()}")

        # Check if file exists and is not a symlink (for security)
        if not path.exists():
            logger.warning(f"Image file not found: {image_path}")
            return False

        if path.is_symlink():
            logger.warning(f"Blocking symlink for security: {image_path}")
            return False

        # Check file extension
        image_extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".webp",
            ".tiff",
            ".tif",
        ]

        path_lower = str(path).lower()
        has_valid_extension = any(path_lower.endswith(ext) for ext in image_extensions)
        logger.debug(
            f"File extension check - path: {path_lower}, valid: {has_valid_extension}"
        )

        if not has_valid_extension:
            logger.warning(f"File does not appear to be an image: {image_path}")
            return False

        # Check file size
        file_size = path.stat().st_size
        max_size = max_size_mb * 1024 * 1024
        logger.debug(
            f"File size check - size: {file_size} bytes, max: {max_size} bytes"
        )

        if file_size > max_size:
            logger.warning(f"Image file too large ({file_size} bytes): {image_path}")
            return False

        logger.debug(f"Image validation successful: {image_path}")
        return True

    except Exception as e:
        logger.error(f"Error validating image file {image_path}: {e}")
        return False


async def insert_text_content(
    lightrag,
    input: str | list[str],
    split_by_character: str | None = None,
    split_by_character_only: bool = False,
    ids: str | list[str] | None = None,
    file_paths: str | list[str] | None = None,
):
    """
    Insert pure text content into LightRAG

    Args:
        lightrag: LightRAG instance
        input: Single document string or list of document strings
        split_by_character: if split_by_character is not None, split the string by character, if chunk longer than
        chunk_token_size, it will be split again by token size.
        split_by_character_only: if split_by_character_only is True, split the string by character only, when
        split_by_character is None, this parameter is ignored.
        ids: single string of the document ID or list of unique document IDs, if not provided, MD5 hash IDs will be generated
        file_paths: single string of the file path or list of file paths, used for citation
    """
    logger.info("Starting text content insertion into LightRAG...")
    print(f"\n[DBUG] === INSERT_TEXT_CONTENT START ===")
    print(f"[DBUG] Input length: {len(input) if isinstance(input, str) else 'list'}")
    print(f"[DBUG] File paths: {file_paths}")
    print(f"[DBUG] IDs: {ids}")

    # Use LightRAG's insert method with all parameters
    print(f"[DBUG] Calling lightrag.ainsert()...")
    await lightrag.ainsert(
        input=input,
        file_paths=file_paths,
        split_by_character=split_by_character,
        split_by_character_only=split_by_character_only,
        ids=ids,
    )
    print(f"[DBUG] ainsert() completed!")

    logger.info("Text content insertion complete")
    print(f"[DBUG] === INSERT_TEXT_CONTENT END ===\n")


async def insert_text_content_with_multimodal_content(
    lightrag,
    input: str | list[str],
    multimodal_content: list[dict[str, any]] | None = None,
    split_by_character: str | None = None,
    split_by_character_only: bool = False,
    ids: str | list[str] | None = None,
    file_paths: str | list[str] | None = None,
    scheme_name: str | None = None,
):
    """
    Insert pure text content into LightRAG

    Args:
        lightrag: LightRAG instance
        input: Single document string or list of document strings
        multimodal_content: Multimodal content list (optional)
        split_by_character: if split_by_character is not None, split the string by character, if chunk longer than
        chunk_token_size, it will be split again by token size.
        split_by_character_only: if split_by_character_only is True, split the string by character only, when
        split_by_character is None, this parameter is ignored.
        ids: single string of the document ID or list of unique document IDs, if not provided, MD5 hash IDs will be generated
        file_paths: single string of the file path or list of file paths, used for citation
        scheme_name: scheme name (optional)
    """
    logger.info("Starting text content insertion into LightRAG...")

    # Use LightRAG's insert method with all parameters
    try:
        await lightrag.ainsert(
            input=input,
            multimodal_content=multimodal_content,
            file_paths=file_paths,
            split_by_character=split_by_character,
            split_by_character_only=split_by_character_only,
            ids=ids,
            scheme_name=scheme_name,
        )
    except Exception as e:
        logger.info(f"Error: {e}")
        logger.info(
            "If the error is caused by the ainsert function not having a multimodal content parameter, please update the raganything branch of lightrag"
        )

    logger.info("Text content insertion complete")


def get_processor_for_type(modal_processors: Dict[str, Any], content_type: str):
    """
    Get appropriate processor based on content type

    Args:
        modal_processors: Dictionary of available processors
        content_type: Content type

    Returns:
        Corresponding processor instance
    """
    # Direct mapping to corresponding processor
    if content_type == "image":
        return modal_processors.get("image")
    elif content_type == "table":
        return modal_processors.get("table")
    elif content_type == "equation":
        return modal_processors.get("equation")
    else:
        # For other types, use generic processor
        return modal_processors.get("generic")


def get_processor_supports(proc_type: str) -> List[str]:
    """Get processor supported features"""
    supports_map = {
        "image": [
            "Image content analysis",
            "Visual understanding",
            "Image description generation",
            "Image entity extraction",
        ],
        "table": [
            "Table structure analysis",
            "Data statistics",
            "Trend identification",
            "Table entity extraction",
        ],
        "equation": [
            "Mathematical formula parsing",
            "Variable identification",
            "Formula meaning explanation",
            "Formula entity extraction",
        ],
        "generic": [
            "General content analysis",
            "Structured processing",
            "Entity extraction",
        ],
    }
    return supports_map.get(proc_type, ["Basic processing"])


def get_vision_model_func() -> Optional[Callable]:
    """
    Create vision model function from environment variables.
    
    Checks for VLM_* environment variables and creates an appropriate
    vision_model_func if configured. Returns None if no VLM is configured.
    
    Environment Variables:
        VLM_BINDING: Vision model binding type (currently only 'ollama' supported)
        VLM_MODEL: Vision model name (e.g., 'qwen3-vl:2b')
        VLM_BINDING_HOST: VLM service URL (e.g., 'http://localhost:11434')
        VLM_TIMEOUT: Request timeout in seconds (default: 60)
    
    Returns:
        Callable or None: Vision model function if VLM is configured, None otherwise
    """
    # Check if VLM is configured
    vlm_binding = os.getenv("VLM_BINDING", "").strip().lower()
    vlm_model = os.getenv("VLM_MODEL", "").strip()
    vlm_host = os.getenv("VLM_BINDING_HOST", "").strip()
    vlm_timeout = int(os.getenv("VLM_TIMEOUT", "60"))
    
    # If any required variable is missing, return None
    if not vlm_binding or not vlm_model or not vlm_host:
        logger.info("VLM not configured (missing VLM_BINDING, VLM_MODEL, or VLM_BINDING_HOST)")
        return None
    
    logger.info(f"Creating vision_model_func for {vlm_binding}/{vlm_model} at {vlm_host}")
    
    if vlm_binding == "ollama":
        return _create_ollama_vision_func(vlm_model, vlm_host, vlm_timeout)
    else:
        logger.warning(f"Unsupported VLM binding: {vlm_binding}. Only 'ollama' is supported.")
        return None


async def _create_ollama_vision_func(model: str, host: str, timeout: int) -> Callable:
    """
    Create Ollama-based vision model function using OpenAI-compatible API.
    
    Args:
        model: Ollama model name (e.g., 'qwen3-vl:2b')
        host: Ollama service URL (e.g., 'http://localhost:11434')
        timeout: Request timeout in seconds
    
    Returns:
        Callable: Async function that can process both single image and multimodal messages
    """
    import aiohttp
    import json
    
    # Use OpenAI-compatible endpoint
    base_url = host.rstrip('/')
    if not base_url.endswith('/v1'):
        base_url = f"{base_url}/v1"
    chat_url = f"{base_url}/chat/completions"
    
    async def ollama_vision_func(
        prompt: str,
        system_prompt: str = None,
        history_messages: list = [],
        image_data: str = None,
        messages: list = None,
        **kwargs
    ) -> str:
        """
        Ollama vision model function supporting both single image and multimodal messages.
        Uses OpenAI-compatible API format.
        
        Args:
            prompt: Text prompt (used in single image mode)
            system_prompt: System prompt
            history_messages: Conversation history
            image_data: Base64 encoded image (single image mode)
            messages: Complete message list (multimodal mode)
            **kwargs: Additional parameters
        
        Returns:
            str: Model response text
        """
        
        try:
            if messages:
                # Mode 2: Multimodal messages (for VLM enhanced query)
                # Messages are already in OpenAI format
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": False,
                }
            elif image_data:
                # Mode 1: Single image (for ImageModalProcessor)
                # Build messages in OpenAI format
                msg_list = []
                if system_prompt:
                    msg_list.append({"role": "system", "content": system_prompt})
                
                # Add user message with text and image
                msg_list.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                })
                
                payload = {
                    "model": model,
                    "messages": msg_list,
                    "stream": False,
                }
            else:
                raise ValueError("Either image_data or messages must be provided")
            
            # Make request to Ollama OpenAI-compatible endpoint
            async with aiohttp.ClientSession() as session:
                async with session.post(chat_url, json=payload, timeout=timeout) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Ollama API error: {resp.status} - {error_text}")
                    
                    result = await resp.json()
                    return result["choices"][0]["message"]["content"]
        
        except Exception as e:
            logger.error(f"Ollama vision model call failed: {e}")
            raise
    
    return ollama_vision_func
