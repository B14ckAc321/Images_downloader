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

from utils import convert_to_grayscale_async, fetch, fetch_image, parse_image_urls, save_image, follow_redirect
import aiohttp
import argparse
import asyncio
import logging
import os


"""
Asyncio Website Image Scraper
This script scrapes images from a list of URLs and optionally converts them to grayscale.
"""

__authors__ = "Noam Maissen, Baptiste Roland"
__date__ = "20.06.2024"
__version__ = "0.1.0"
__emails__ = "noam.maissen@edu.hefr.ch, baptiste.roland@edu.hefr.ch"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def scrape_images(url_list, dest_dir, convert_gray):
    """
    Scrape images from a list of URLs and save them to the destination directory.

    :param url_list: List of URLs to scrape images from
    :type url_list: list
    :param dest_dir: Directory to save the downloaded images
    :type dest_dir: str
    :param convert_gray: Flag to indicate if images should be converted to grayscale
    :type convert_gray: bool
    """
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in url_list:
            tasks.append(process_url(session, url, dest_dir, convert_gray))
        await asyncio.gather(*tasks)


async def process_url(session, url, dest_dir, convert_gray):
    """
    Process a single URL to fetch and download images.

    :param session: Aiohttp client session
    :type session: aiohttp.ClientSession
    :param url: URL to process
    :type url: str
    :param dest_dir: Directory to save the downloaded images
    :type dest_dir: str
    :param convert_gray: Flag to indicate if images should be converted to grayscale
    :type convert_gray: bool
    """
    logger.info(f"Processing URL: {url}")
    redirected_url = await follow_redirect(session, url)  # Follow the redirection
    html = await fetch(session, redirected_url)  # Fetch the HTML content
    if not html:
        logger.warning(f"No HTML content fetched for URL: {redirected_url}")
        return
    image_urls = await parse_image_urls(html, redirected_url)
    if not os.path.exists(dest_dir):  # Create the destination directory if it does not exist
        os.makedirs(dest_dir)
    tasks = []
    for img_url in image_urls:  # Download and save each image
        tasks.append(download_and_save_image(session, img_url, dest_dir, convert_gray))
    await asyncio.gather(*tasks)


async def download_and_save_image(session, img_url, dest_dir, convert_gray):
    """
    Download an image and save it to the destination directory.

    :param session: Aiohttp client session
    :type session: aiohttp.ClientSession
    :param img_url: Image URL to download
    :type img_url: str
    :param dest_dir: Directory to save the downloaded image
    :type dest_dir: str
    :param convert_gray: Flag to indicate if image should be converted to grayscale
    :type convert_gray: bool
    """
    logger.info(f"Downloading image URL: {img_url}")
    image_data, updated_url = await fetch_image(session, img_url)
    if not image_data:
        logger.warning(f"No image data fetched for URL: {img_url}")
        return
    if convert_gray:  # Convert the image to grayscale
        image_data = await convert_to_grayscale_async(image_data)
    filename = os.path.join(dest_dir, os.path.basename(updated_url))  # Save the image to the destination directory
    await save_image(image_data, filename)


def load_urls(file_path):
    """
    Load a list of URLs from a file.

    :param file_path: Path to the file containing URLs
    :type file_path: str
    :return: List of URLs
    :rtype: list
    """
    try:
        with open(file_path, "r") as file:  # Read the URLs from the file
            urls = [line.strip() for line in file.readlines()]
        logger.info(f"Loaded {len(urls)} URLs from {file_path}")
        return urls
    except Exception as e:
        logger.error(f"Error loading URLs from {file_path}: {e}")
        return []


def main():
    """
    Main function to parse arguments and start the image scraping process.
    """
    parser = argparse.ArgumentParser(description="Asyncio Website Image Scraper")
    parser.add_argument("--URLlist", type=str, default="./urls.txt", help="File containing the URL list")
    parser.add_argument("--nc", action="store_true", help="Do not convert images to grayscale")
    parser.add_argument("--dest", type=str, default="../images", help="Destination directory for downloaded images")
    args = parser.parse_args()

    url_list = load_urls(args.URLlist)
    asyncio.run(scrape_images(url_list, args.dest, not args.nc))


if __name__ == "__main__":
    main()
