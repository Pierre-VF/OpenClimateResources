"""
This python script screens resources linked to, and ensures that they're still alive
"""

import logging
import os
import re

import requests
from tqdm import tqdm

SESSION = requests.Session()
NAVIGATOR_HEADERS = {
    "User-Agent": "Mozilla/5.0",
}

markdown_file = "README.md"

# ------------------------------------------------------------------------------------
# Reads the file
# ------------------------------------------------------------------------------------
if os.path.exists(markdown_file):
    file_io_path = markdown_file
elif os.path.exists(f"../{markdown_file}"):
    file_io_path = f"../{markdown_file}"
else:
    raise FileNotFoundError("Unable to find readme file")

logging.info(f"Reading file: {file_io_path}")
with open(file_io_path, "r") as f:
    md_content = f.read()

# ------------------------------------------------------------------------------------
# Checks all links for obsolete references
# ------------------------------------------------------------------------------------


# Finding links in markdown file
def find_links_in_markdown(markdown_text: str) -> dict[str, str]:
    pattern = r"\[([^\]]+)\]\(([^\)]+)\)|\[([^\]]+)\]\s*\[([^\]]*)\]"
    out = re.findall(pattern, markdown_text)
    return {i[0]: i[1] for i in out}


logging.info("Finding all links in markdown file")
links = find_links_in_markdown(md_content)

external_links = [
    i
    for i in list(links.values())
    if i.startswith("https://") or i.startswith("http://")
]

# Identifying invalid and redirected links
logging.info("Checking all links via web requests")
invalid_urls = []
redirected_urls = {}
forbidden_urls = []

for url_i in tqdm(external_links):
    r = SESSION.get(url_i, allow_redirects=False, headers=NAVIGATOR_HEADERS)
    status_code = r.status_code
    if (status_code // 100) == 2:
        pass  # Nothing to declare
    elif status_code == 404:
        invalid_urls.append(url_i)
        logging.warning(f"Invalid URL: {url_i}")
    elif (status_code // 100) == 3:
        next_url = r.next.url
        redirected_urls[url_i] = next_url
        logging.warning(f"Redirecting {url_i} to {next_url}")
    elif status_code == 403:
        forbidden_urls.append(url_i)
    else:
        logging.warning(f"Error on {url_i} : status={status_code}")


# ------------------------------------------------------------------------------------
# Writing updates in file
# ------------------------------------------------------------------------------------
logging.info("Replacing links")
for i in invalid_urls:
    md_content = md_content.replace(i, "DEAD_URL")
for old_url, new_url in redirected_urls.items():
    md_content = md_content.replace(old_url, new_url)
# and do nothing about the forbidden ones

logging.info(f"Exporting updated file: {file_io_path}")
with open(file_io_path, "w") as f:
    f.write(md_content)

logging.info("Completed")
