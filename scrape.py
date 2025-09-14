import itertools
from typing import Optional, List, Dict, Any

import requests
from lxml import html
from lxml.etree import _Element


session = requests.session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0',
})


def load_older_comments(last_parent_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Loads more comments using the given parameters.

    Args:
        last_parent_id: ID of the last parent comment loaded

    Returns:
        Dictionary of parsed top-level comments with comment IDs as keys
    """
    # https://www.doctorofcredit.com/complete-list-of-ways-to-close-bank-accounts-at-each-bank/#comments
    BANK_ACCOUNT_CLOSURES_POST = 24906
    data = {
        "postId": BANK_ACCOUNT_CLOSURES_POST,
        "action": "wpdLoadMoreComments",
        "sorting": "newest",
        "wpdType": "",
        **({"lastParentId": last_parent_id} if last_parent_id is not None else {})
    }

    comments_endpoint = "https://www.doctorofcredit.com/wp-admin/admin-ajax.php"
    response = session.post(
        comments_endpoint,
        # hack to get filename that requests would usually add off the multi-part form
            files={k: (None, v) for k, v in data.items()}
    )

    response.raise_for_status()
    comment_html = response.json()["data"]["comment_list"]
    if len(comment_html) == 0:
        return {}

    parsed_html = html.fromstring(
        comment_html,
        base_url="https://www.doctorofcredit.com"
    )

    return parse_top_level_comments(parsed_html)


def parse_top_level_comments(html_element: _Element) -> Dict[str, Any]:
    """
    Parse only top-level comments from the HTML.

    Args:
        html_element: Parsed HTML element containing comments

    Returns:
        Dictionary of parsed comments with comment IDs as keys
    """
    comments = {}

    top_level_comments = html_element.cssselect(".wpd_comment_level-1")
    for comment_el in top_level_comments:

        date_el = comment_el.cssselect(".wpd-comment-date")
        date = date_el[0].text_content().strip() if date_el else None

        text_el = comment_el.cssselect(".wpd-comment-text")
        text = text_el[0].text_content().strip() if text_el else None

        url_el = comment_el.cssselect(".wpd-comment-link span[data-wpd-clipboard]")
        url = url_el[0].get("data-wpd-clipboard") if url_el else None

        comment_id = None
        if url and "#comment-" in url:
            comment_id = url.split("#comment-")[1]

        # Extract author name
        author_el = comment_el.cssselect(".wpd-comment-author")
        author = author_el[0].text_content().strip() if author_el else "Anonymous"

        comments[comment_id] = {
            "url": url,
            "author": author,
            "date": date,
            "text": text,
        }

    return comments


def get_all_comments() -> Dict[str, Any]:
    """
    Retrieve all top-level comments by making multiple requests.
    
    Returns:
        Dictionary of all top-level comments with comment IDs as keys
    """
    all_comments = {}
    last_id = None

    for page in itertools.count():
        comments_after_last_id = load_older_comments(last_id)
        if not comments_after_last_id:
            break

        all_comments.update(comments_after_last_id)
        last_id = next(iter(reversed(comments_after_last_id.keys())))
        print(page, end="\r")

    return all_comments


if __name__ == "__main__":
    # Example: load and parse the first batch of comments
    comments = get_all_comments()
    print(f"Found {len(comments)} top-level comments")
    # Show the first 5 comments
    for i, (comment_id, comment) in enumerate(list(comments.items())[:5]):
        print(f"[{comment_id}] {comment['author']} ({comment['date']}): {comment['text'][:100]}...")
