#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2024, School of Engineering and Architecture of Fribourg
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from PIL import Image, UnidentifiedImageError
from urllib.parse import urljoin, urlparse
import aiofiles
import io
import os
import logging

"""
Image Scraper Utilities
This module contains utility functions for scraping and processing images from web pages.
"""

__authors__ = "Noam Maissen, Baptiste Roland"
__date__ = "20.06.2024"
__version__ = "0.1.0"
__emails__ = "noam.maissen@edu.hefr.ch, baptiste.roland@edu.hefr.ch"
__name__ = "image_scraper"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def follow_redirect(session, url):
    """
    Follow redirects for a given URL and return the final URL.

    :param session: Aiohttp client session
    :type session: aiohttp.ClientSession
    :param url: Initial URL to follow
    :type url: str
    :return: Final redirected URL
    :rtype: str
    """
    try:
        async with session.get(url) as response:
            response.raise_for_status()  # Raise exception for HTTP errors
            redirected_url = str(response.url)
            logger.info(f"Redirected URL: {redirected_url}")
            return redirected_url
    except Exception as e:
        logger.error(f"Error following redirection {url}: {e}")
        return url


async def fetch(session, url):
    """
    Fetch the HTML content from a given URL.

    :param session: Aiohttp client session
    :type session: aiohttp.ClientSession
    :param url: URL to fetch
    :type url: str
    :return: HTML content of the URL
    :rtype: str or None
    """
    try:
        async with session.get(url) as response:
            response.raise_for_status()  # Raise exception for HTTP errors
            logger.info(f"Successfully fetched URL: {url}")
            return await response.text()
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None


def get_extension_from_content_type(content_type):
    """
    Get the file extension from the content type.

    :param content_type: MIME type of the content
    :type content_type: str
    :return: File extension based on the content type
    :rtype: str or None
    """
    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"
    elif "png" in content_type:
        return ".png"
    elif "gif" in content_type:
        return ".gif"
    elif "bmp" in content_type:
        return ".bmp"
    elif "webp" in content_type:
        return ".webp"
    else:
        return None


def add_extension_if_missing(url, content_type):
    """
    Add file extension to the URL if it is missing based on the content type.

    :param url: Original URL
    :type url: str
    :param content_type: MIME type of the content
    :type content_type: str
    :return: Updated URL with the correct file extension
    :rtype: str
    """
    parsed_url = urlparse(url)
    extension = os.path.splitext(parsed_url.path)[1]
    if not extension:
        new_extension = get_extension_from_content_type(content_type)
        if new_extension:
            url += new_extension
            logger.info(f"Added extension {new_extension} to URL: {url}")
    return url


async def fetch_image(session, url):
    """
    Fetch image data from a given URL.

    :param session: Aiohttp client session
    :type session: aiohttp.ClientSession
    :param url: URL to fetch the image from
    :type url: str
    :return: Image data and updated URL with extension
    :rtype: tuple (bytes, str)
    """
    try:
        async with session.get(url) as response:
            response.raise_for_status()  # Raise exception for HTTP errors
            content_type = response.content_type
            if "image" in content_type:
                url = add_extension_if_missing(url, content_type)
                logger.info(f"Successfully fetched image URL: {url} with content type {content_type}")
                return await response.read(), url
            else:
                content_snippet = await response.text()
                logger.warning(
                    f"Non-image content type at {url}: {content_type}, content snippet: {content_snippet[:100]}"
                )
                return None, url
    except Exception as e:
        logger.error(f"Error fetching image {url}: {e}")
        return None, url


async def parse_image_urls(html, base_url):
    """
    Parse image URLs from the HTML content.

    :param html: HTML content of the page
    :type html: str
    :param base_url: Base URL of the page to resolve relative URLs
    :type base_url: str
    :return: List of full image URLs
    :rtype: list
    """
    soup = BeautifulSoup(html, "html.parser")
    image_urls = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            full_url = urljoin(base_url, src)
            image_urls.append(full_url)
    logger.info(f"Found {len(image_urls)} image URLs on {base_url}")
    return image_urls


async def save_image(data, filepath):
    """
    Save image data to a file.

    :param data: Image data to save
    :type data: bytes
    :param filepath: Path to save the image
    :type filepath: str
    """
    try:
        async with aiofiles.open(filepath, "wb") as file:
            await file.write(data)
        logger.info(f"Successfully saved image to {filepath}")
    except Exception as e:
        logger.error(f"Error saving image to {filepath}: {e}")


def convert_to_grayscale(image_data):
    """
    Convert image data to grayscale.

    :param image_data: Original image data
    :type image_data: bytes
    :return: Grayscale image data
    :rtype: bytes
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        gray_image = image.convert("LA")
        byte_arr = io.BytesIO()
        gray_image.save(byte_arr, format=image.format)
        logger.info("Successfully converted image to grayscale")
        return byte_arr.getvalue()
    except UnidentifiedImageError as e:
        logger.error(f"Error converting image to grayscale: {e}")
        return image_data


async def convert_to_grayscale_async(image_data):
    """
    Convert image data to grayscale asynchronously.

    :param image_data: Original image data
    :type image_data: bytes
    :return: Grayscale image data
    :rtype: bytes
    """
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, convert_to_grayscale, image_data)
