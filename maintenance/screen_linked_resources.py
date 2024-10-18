"""
This python script screens resources linked to, and ensures that they're still alive
"""

import os
import re

import requests

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


links = find_links_in_markdown(md_content)

external_links = [
    i
    for i in list(links.values())
    if i.startswith("https://") or i.startswith("http://")
]

# Identifying invalid and redirected links
invalid_urls = []
redirected_urls = {}
forbidden_urls = []

for url_i in external_links:
    r = SESSION.get(url_i, allow_redirects=False, headers=NAVIGATOR_HEADERS)
    status_code = r.status_code
    if (status_code // 100) == 2:
        pass  # Nothing to declare
    elif status_code == 404:
        invalid_urls.append(url_i)
    elif (status_code // 100) == 3:
        next_url = r.next.url
        redirected_urls[url_i] = next_url
        print(f"Redirecting {url_i} to {next_url}")
    elif status_code == 403:
        forbidden_urls.append(url_i)
    else:
        print(f"Error {url_i} : status={status_code} / resp={r.text}")


# ------------------------------------------------------------------------------------
# Writing updates in file
# ------------------------------------------------------------------------------------

for i in invalid_urls:
    md_content = md_content.replace(i, "DEAD_URL")
for old_url, new_url in redirected_urls.items():
    md_content = md_content.replace(old_url, new_url)
# and do nothing about the forbidden ones

with open(file_io_path, "w") as f:
    f.write(md_content)
