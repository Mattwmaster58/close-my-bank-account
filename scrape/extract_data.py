import json
import os
from datetime import datetime
from itertools import zip_longest
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

from scrape import Comment

class ClosureAttempt(BaseModel):
    success: bool
    bank_name: str
    method: Literal["chat", "phone", "in-branch", "0-balance", "secure-message"]

class ClosureData(BaseModel):
    closure_attempts: list[ClosureAttempt]

class ExtractedCommentData(BaseModel):
    commentId: str
    date: int  # Unix timestamp
    extracted_data: ClosureData


load_dotenv()
ai_client = genai.Client(api_key=os.getenv('GENAI_API_KEY'))

def extract_comment_data(comment: Comment) -> ClosureData:
    prompt = f"""
    Based on provided comment text, provide a list of bank account closure attempts.
     - It is possible there is 0 closure attempts in a comment
     - If a comment is neutrally worded, assume a positive result (ie, successful closure)

    Here's a list of banks your should prefer, but are not required to choose from:

    1st United Bank
    Abington Bank
    Alliant
    All America Bank/Redneck Bank
    Ally
    Amalgamated Bank
    Amboy
    Andigo Credit Union
    Associated Bank
    Astoria Bank
    Bank of America
    BB&T
    Bank Of The West
    Bank & Trust
    BB&T
    BBVA
    Blue Hills Bank
    Bluevine
    BMO Harris
    BMT (Bryn Mawr Trust)
    Bridgeview Bank
    Cambridge Savings Bank
    CampusUSA
    Capital Bank
    Capital One 360
    Chase
    Chime
    Christian Community Credit Union
    CIT Bank
    Citi
    Citadel Credit Union
    Citizens Bank
    City National Bank (WV)
    Columbia Bank (NJ)
    Columbia Bank  (WA, OR, ID)
    Comerica
    Credit Union West
    Dollar Bank
    Discover
    Easthampton Savings Bank (BankESB)
    Elements
    FCB South County Bank
    Fidelity Bank
    Fifth Third
    First America Bank
    FirstBank
    First Citizens Bank
    First Federal Bank
    First Horizon
    First Merchants Bank
    First National Bank
    First National Bank of PA
    First Niagara
    First Tech Federal Credit Union
    First Tennessee
    Five Star Bank
    Flushing Bank
    Fulton Bank
    Gesa Credit Union
    Hancock Whitney
    Hanmi Bank
    Home Savings Bank
    HomeStreet
    HSBC
    Huntington
    Iberia Bank
    Incredible Bank
    Investors Bank
    KeyBank
    KeyPoint
    Lakeland Bank
    LegacyTexas Bank
    LevelOne Bank
    Liberty Bank
    Lili
    Marcus By Goldman Sachs
    Maxx By Cedar Rapids
    MECU Credit Union
    Memory Bank
    MidFirst Bank
    Midland States Bank
    Monifi
    Mountain America Credit Union
    M&T
    Nationwide
    Navy Federal Credit Union (NFCU)
    NBKC
    Northpointe
    Northshore Credit Union
    Northwest
    NYCB Family Of Banks
    Ocean First
    Old National Bank
    Orion Federal Credit Union
    PeoplesBank
    Pinnacle Bank
    Pinnacle Bank (Texas)
    PNC
    Popular Community
    Provident Bank
    Quontic
    Quorum FCU
    Radius Bank
    Regions Bank
    Republic Bank
    Ridgewood Savings Bank
    Rockland Trust Bank
    Salem Five
    Sandy Spring Bank
    Santander
    Seacoast Bank
    SEFCU
    SFGI
    SkyOne Federal Credit Union
    South Shore Bank
    S&T Bank
    Suffolk Credit Union
    SunTrust
    Synovus
    Talmer Bank
    TCF Bank
    Tech CU
    TD Bank
    TIAA Direct
    Truist
    UFB Direct
    Unify
    Union Bank
    Union Bank & Trust
    United Bank
    USAA
    U.S Bank
    Valley National Bank
    VantageWest
    Varo Money
    Verity Credit Union
    Webster Bank
    Wells Fargo
    Westfield Bank (MA)
    Wings Credit Union
    Wintrust Bank

    Comment:'{comment.text}'
    """
    response = ai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": ClosureData,
        },
    )
    return response.parsed


def update_extracted_data():
    """
     - Reads comments.jsonl
     - for comment NOT present in extracted.jsonl, attempts to use AI to extract the data
    """
    base_path = Path(__file__).parent
    extracted_data_path = base_path / "extracted.jsonl"
    comments_path = base_path / "comments.jsonl"

    comments = []
    for line in comments_path.read_text().splitlines():
        comments.append(Comment.model_validate_json(line.strip()))

    # assume consistent ordering between comments.jsonl/extracted.jsonl
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
            extracted_comment_data = ExtractedCommentData(commentId=comment.id, date=comment.date, extracted_data=closure_data)
            with open(extracted_data_path, "a") as extracted_data_file:
                extracted_data_file.write(f"{extracted_comment_data.model_dump_json()}\n")



if __name__ == '__main__':
    update_extracted_data()
