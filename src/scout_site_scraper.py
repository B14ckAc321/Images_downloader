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

import aiohttp
import argparse
import asyncio
import os
from bs4 import BeautifulSoup
from image_scraper import download_and_save_image, follow_redirect, fetch, parse_image_urls

async def fetch_album_urls(session, base_url):
    """
    Fetch album URLs from the main category page, including nested sub-albums.

    :param session: Aiohttp client session
    :type session: aiohttp.ClientSession
    :param base_url: The base URL of the category page
    :type base_url: str
    :return: List of tuples containing album URLs and their corresponding titles
    :rtype: list of tuples
    """
    album_urls = []
    html = await fetch(session, base_url)
    soup = BeautifulSoup(html, 'html.parser')
    category_links = soup.select('dl#mbCategories ul li a')
    
    for link in category_links:
        album_url = link.get('href')
        album_title = link.get_text(strip=True)
        album_urls.append((album_url, album_title))
    
    return album_urls

async def scrape_album_images_bfs(session, base_url, album_url, album_title, dest_dir, max_depth=2):
    """
    Scrape images from albums using breadth-first search and save them to a designated folder,
    handling pagination for albums that span multiple pages.

    :param session: Aiohttp client session
    :type session: aiohttp.ClientSession
    :param base_url: The base URL of the site
    :type base_url: str
    :param album_url: The relative URL of the album
    :type album_url: str
    :param album_title: The title of the album
    :type album_title: str
    :param dest_dir: Destination directory for downloaded images
    :type dest_dir: str
    :param max_depth: Maximum depth to avoid excessive recursion
    :type max_depth: int
    """
    visited = set()
    queue = [(album_url, album_title, dest_dir, 0)]  # Initialize the queue with the root album

    while queue:
        current_url, current_title, current_dir, current_depth = queue.pop(0)

        # Avoid revisiting the same album
        full_album_url = os.path.join(base_url, current_url)
        if full_album_url in visited:
            continue
        visited.add(full_album_url)

        # Generate unique directory for each album
        album_dest_dir = os.path.join(current_dir, current_title.replace(' ', '_'))
        if not os.path.exists(album_dest_dir):
            os.makedirs(album_dest_dir)

        while full_album_url:
            redirected_url = await follow_redirect(session, full_album_url)
            html = await fetch(session, redirected_url)

            if not html:
                # Log the issue and break the loop if HTML is not fetched
                print(f"Failed to fetch HTML from {full_album_url}")
                break

            # Parse and download images in the current page of the album
            image_urls = await parse_image_urls(html, redirected_url)
            tasks = [download_and_save_image(session, img_url, album_dest_dir, False) for img_url in image_urls]
            await asyncio.gather(*tasks)

            # Find and queue the next page if available
            soup = BeautifulSoup(html, 'html.parser')
            next_page_link = soup.select_one('span.navPrevNext a[rel="next"]')  # Selector for the "Next" link
            if next_page_link and next_page_link.get('href'):
                full_album_url = os.path.join(base_url, next_page_link.get('href'))
            else:
                full_album_url = None

        # Avoid further processing if maximum depth is reached
        if current_depth >= max_depth:
            continue

        # Find and queue sub-albums
        soup = BeautifulSoup(html, 'html.parser')
        sub_album_links = soup.select('ul ul li a')  # Select only nested sub-albums
        for sub_album_link in sub_album_links:
            sub_album_url = sub_album_link.get('href')
            sub_album_title = sub_album_link.get_text(strip=True)
            queue.append((sub_album_url, sub_album_title, album_dest_dir, current_depth + 1))


async def download_scout(dest_dir, base_url):
    """
    Download images from all albums on the category page, including nested sub-albums.

    :param dest_dir: Destination directory for downloaded images
    :type dest_dir: str
    :param base_url: Base URL of the category page
    :type base_url: str
    """
    async with aiohttp.ClientSession() as session:
        album_urls = await fetch_album_urls(session, base_url)
        tasks = []
        for album_url, album_title in album_urls:
            # Use the destination directory to manage each top-level album
            tasks.append(scrape_album_images_bfs(session, base_url, album_url, album_title, dest_dir))
        await asyncio.gather(*tasks)

def main():
    """
    Main function to parse arguments and start the image scraping process.
    """
    parser = argparse.ArgumentParser(description="Asyncio Website Image Scraper for Albums")
    parser.add_argument("--base_url", type=str, default="https://foto.scoutlocarno.ch/", help="Base URL of the site")
    parser.add_argument("--dest", type=str, default="../images", help="Destination directory for downloaded images")
    args = parser.parse_args()

    asyncio.run(download_scout(args.dest, args.base_url))

if __name__ == "__main__":
    main()
