import json
import os
import random
import time
from itertools import zip_longest
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from pydantic import BaseModel

from scrape import Comment


class ClosureAttempt(BaseModel):
    success: bool
    bank_name: str
    method: Literal["chat", "secure-message", "phone", "in-branch", "0-balance", "on-platform", "unknown"]


class ClosureData(BaseModel):
    closure_attempts: list[ClosureAttempt]


class ExtractedCommentData(BaseModel):
    commentId: str
    timestamp: int
    extracted_data: ClosureData


class BankAttempt(BaseModel):
    comment_id: str
    method: str
    success: bool
    timestamp: int


load_dotenv()

def _get_ai_client():
    """Lazy-init the AI client so the module doesn't crash on import if no key is set."""
    key = os.getenv('GOOGLE_API_KEY')
    if not key:
        return None
    return genai.Client(api_key=key)


# HTTP statuses worth retrying with backoff. Anything else (auth errors,
# bad requests, ...) fails fast so real problems surface immediately.
_RETRYABLE_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}


def _is_retryable_api_error(exc: Exception) -> bool:
    code = getattr(exc, "code", None)
    if code is None:
        code = getattr(exc, "status_code", None)
    if code is None:
        # Unknown error shape — retry only server-side error types.
        return isinstance(exc, genai_errors.ServerError)
    try:
        code = int(code)
    except (TypeError, ValueError):
        return False
    return code in _RETRYABLE_STATUS_CODES


def _send_with_retry(send_fn, *, max_attempts=6, base_delay=10.0):
    """Call send_fn(), retrying transient Gemini API errors with exponential backoff.

    The Gemini API occasionally returns 503 "high demand" spikes; without a
    retry the whole nightly workflow fails. Waits ~10s, ~20s, ~40s, ... with
    jitter between attempts.
    """
    delay = base_delay
    for attempt in range(1, max_attempts + 1):
        try:
            return send_fn()
        except genai_errors.APIError as exc:
            if not _is_retryable_api_error(exc) or attempt == max_attempts:
                raise
            sleep_s = delay + random.uniform(0, delay)
            print(
                f"Gemini API transient error (attempt {attempt}/{max_attempts}): {exc}. "
                f"Retrying in {sleep_s:.0f}s..."
            )
            time.sleep(sleep_s)
            delay *= 2


def get_existing_banks() -> list[str]:
    """Load existing bank names from by_bank.json if it exists."""
    base_path = Path(__file__).parent
    by_bank_path = base_path / "by_bank.json"

    if by_bank_path.exists():
        with open(by_bank_path) as f:
            data = json.load(f)
            return sorted(set(data.keys()))

    return []


def extract_comment_data(comment: Comment) -> ClosureData:
    client = _get_ai_client()
    if client is None:
        raise RuntimeError("GOOGLE_API_KEY is not set — cannot run extraction")
    existing_banks = get_existing_banks()
    bank_list_text = "\n".join(existing_banks)
    prompt = f"""
    Based on provided comment text, provide a list of bank account closure attempts.
     - It is possible there is 0 closure attempts in a comment
     - If a comment is neutrally worded, assume a positive result (ie, successful closure)
     - on-platform refers to being able to close the account on the site or app, without additional human interaction
     - When matching banks, treat names with and without "Bank" suffix as the same institution

    Here's a list of banks you should prefer, but are not required to choose from:

    {bank_list_text}

    Comment:'{comment.text}'
    """
    def _do_send():
        return client.chats.create(
            model="gemini-3.5-flash",
            config={
                "response_mime_type": "application/json",
                "response_schema": ClosureData,
            },
        ).send_message(prompt)

    response = _send_with_retry(_do_send)
    return response.parsed


def update_extracted_data():
    """
     - Reads comments.jsonl
     - for comment NOT present in extracted.jsonl, attempts to use AI to extract the data
    """
    base_path = Path(__file__).parent
    extracted_data_path = base_path / "comments_extracted.jsonl"
    comments_path = base_path / "comments.jsonl"

    comments = []
    for line in comments_path.read_text().splitlines():
        comments.append(Comment.model_validate_json(line.strip()))

    extracted = []
    if extracted_data_path.exists():
        for line in extracted_data_path.read_text().splitlines():
            extracted.append(ExtractedCommentData.model_validate_json(line.strip()))

    for idx, (comment, extracted_data) in enumerate(zip_longest(comments, extracted)):
        if extracted_data is not None:
            assert comment.id == extracted_data.commentId, "expected consistent ordering between data files"
        else:
            closure_data = extract_comment_data(comment)
            print(f"extracted closure data for {comment.id}: {closure_data}")
            extracted_comment_data = ExtractedCommentData(commentId=comment.id, timestamp=comment.timestamp,
                                                          extracted_data=closure_data)
            with open(extracted_data_path, "a") as extracted_data_file:
                extracted_data_file.write(f"{extracted_comment_data.model_dump_json()}\n")


def create_by_bank_json():
    base_path = Path(__file__).parent
    extracted_data_path = base_path / "comments_extracted.jsonl"
    by_bank_path = base_path / "by_bank.json"

    by_bank: dict[str, list[dict]] = {}

    if extracted_data_path.exists():
        for line in extracted_data_path.read_text().splitlines():
            extracted = ExtractedCommentData.model_validate_json(line.strip())
            for attempt in extracted.extracted_data.closure_attempts:
                bank_attempt = BankAttempt(
                    comment_id=extracted.commentId,
                    method=attempt.method,
                    success=attempt.success,
                    timestamp=extracted.timestamp
                )
                by_bank_name = by_bank.get(attempt.bank_name, [])
                by_bank_name.append(bank_attempt.model_dump())
                by_bank[attempt.bank_name] = by_bank_name

    for bank_name in by_bank:
        by_bank[bank_name].sort(key=lambda x: x['timestamp'])

    sorted_by_bank = dict(sorted(by_bank.items()))

    with open(by_bank_path, "w") as f:
        json.dump(sorted_by_bank, f, indent=2)


if __name__ == '__main__':
    update_extracted_data()
    create_by_bank_json()
