import itertools
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Set, List

import pytz
import requests
from lxml import html
from lxml.etree import _Element, ParserError
from pydantic import BaseModel, field_validator

session = requests.session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0', })


class Comment(BaseModel):
    """Validated comment model with proper date parsing"""
    id: str
    url: Optional[str] = None
    author: str
    date: datetime
    text: str


def load_older_comments(last_parent_id: Optional[int] = None) -> List[Comment]:
    """
    Loads more comments using the given parameters.

    Args:
        last_parent_id: ID of the last parent comment loaded

    Returns:
        List of parsed top-level comments
    """
    # https://www.doctorofcredit.com/complete-list-of-ways-to-close-bank-accounts-at-each-bank/#comments
    BANK_ACCOUNT_CLOSURES_POST = 24906
    data = {"postId": BANK_ACCOUNT_CLOSURES_POST, "action": "wpdLoadMoreComments", "sorting": "newest", "wpdType": "",
            **({"lastParentId": last_parent_id} if last_parent_id is not None else {})}

    comments_endpoint = "https://www.doctorofcredit.com/wp-admin/admin-ajax.php"
    response = session.post(comments_endpoint,
                            # hack to get filename that requests would usually add off the multi-part form
                            files={k: (None, v) for k, v in data.items()})

    response.raise_for_status()
    comment_html = response.json()["data"]["comment_list"]

    try:
        parsed_html = html.fromstring(comment_html, base_url="https://www.doctorofcredit.com")
    except ParserError as e:
        if "document is empty" in str(e).lower():
            return []
        raise e

    return parse_top_level_comments(parsed_html)


def parse_top_level_comments(html_element: _Element) -> List[Comment]:
    """
    Parse only top-level comments from the HTML.

    Args:
        html_element: Parsed HTML element containing comments

    Returns:
        List of parsed comments
    """
    comments = []

    top_level_comments = html_element.cssselect(".wpd_comment_level-1")
    for comment_el in top_level_comments:

        date_el = comment_el.cssselect(".wpd-comment-date")
        date_raw = date_el[0].text_content().strip() if date_el else None

        text_el = comment_el.cssselect(".wpd-comment-text")
        text = text_el[0].text_content().strip() if text_el else None

        url_el = comment_el.cssselect(".wpd-comment-link span[data-wpd-clipboard]")
        url = url_el[0].get("data-wpd-clipboard") if url_el else None

        comment_id = None
        if url and "#comment-" in url:
            comment_id = url.split("#comment-")[1]
        else:
            raise ValueError(f"Unable to parse comment id from url: {url}")

        # Extract author name
        author_el = comment_el.cssselect(".wpd-comment-author")
        author = author_el[0].text_content().strip() if author_el else None

        comment = Comment(id=comment_id, url=url, author=author, date=to_iso_timestamp(date_raw), text=text)
        comments.append(comment)

    return comments


def get_all_comments() -> List[Comment]:
    """
    Retrieve all top-level comments by making multiple requests.

    Returns:
        List of all top-level comments
    """
    all_comments = []
    last_id = None

    for page in itertools.count():
        comments_after_last_id = load_older_comments(last_id)
        if not comments_after_last_id:
            break

        all_comments.extend(comments_after_last_id)
        if comments_after_last_id:
            last_id = comments_after_last_id[-1].id
        print(page, end="\r")

    return all_comments


def to_iso_timestamp(raw: str) -> str:
    # eg "December 30, 2022 17:27"
    pattern = r'(\w+)\s+(\d+),\s+(\d{4})\s+(\d{1,2}):(\d{2})'
    match = re.search(pattern, raw, re.IGNORECASE)
    month, day, year, hour, minute = match.groups()
    month_num = datetime.strptime(month, '%B').month
    # todo: webpage is probably localized to the requester's tz
    # for now, just assume eastern
    return datetime(int(year), month_num, int(day), int(hour), int(minute),
                    tzinfo=pytz.timezone('US/Eastern')).isoformat()


def update_comment_dump(file_path: str = "comments.jsonl") -> List[Comment]:
    """
    Update comment dump by fetching new comments and organizing them chronologically.
    
    Reads existing comments from file, fetches new comments until it finds ones 
    we've already seen, and dumps all comments in chronological order (oldest first).
    
    Args:
        file_path: Path to the JSONL file for comment storage

    Returns:
        List of all comments, sorted chronologically
    """
    file_path = Path(file_path)

    # Keep track of comment IDs we've already seen
    seen_comment_ids: Set[str] = set()
    existing_comments: List[Comment] = []

    # Read existing comments if file exists
    if file_path.exists():
        with file_path.open('r') as f:
            for line in f:
                comment = Comment.model_validate_json(line.strip())
                existing_comments.append(comment)
                seen_comment_ids.add(comment.id)

    print(f"Found {len(existing_comments)} existing comments in {file_path}")

    # Fetch new comments until we encounter an ID we've seen before
    new_comments: List[Comment] = []
    last_id = None

    for page in itertools.count(start=1):  # Start counting from 1 for human-readable output
        print(f"Fetching page {page} of comments...", end="\r")

        comments_batch = load_older_comments(last_id)
        if not comments_batch:
            print("\nNo more comments to fetch")
            break

        if any(comment.id in seen_comment_ids for comment in comments_batch):
            print("Reached previously scraped comments, stopping fetch")
            break

        new_comments.extend(comments_batch)
        last_id = comments_batch[-1].id
        print(f"Page {page}, {len(comments_batch)} comments")

    all_comments = existing_comments + new_comments
    print(f"Total comments: {len(all_comments)} ({len(new_comments)} new)")
    sorted_comments = sorted(all_comments, key=lambda x: x.date)

    if new_comments:
        with file_path.open('w') as f:
            for comment in sorted_comments:
                f.write(comment.model_dump_json() + "\n")
        print(f"Successfully updated {file_path} with comments in chronological order")
    else:
        print(f"No new comments found, file remains unchanged")

    return sorted_comments


if __name__ == "__main__":
    comments = update_comment_dump()
