"""Original multilingual examples for context and long-document checks."""

CONTEXT = {
    "en": (
        "When I reached the station,\n"
        "I realized I had left my ticket at home.\n"
        "My sister brought it to me before the train arrived."
    ),
    "he": (
        "כשחזרתי הביתה,\nמצאתי מכתב על השולחן.\n"
        "הוא הזכיר לי את הקיץ שבילינו יחד."
    ),
    "pl": (
        "Kiedy wróciłam do domu,\nznalazłam list na stole.\n"
        "Przypomniał mi lato, które spędziliśmy razem."
    ),
}


def long_document() -> str:
    """Create 100 distinct paragraphs, exceeding 5,000 English words."""
    return "\n\n".join(
        f"Chapter {number}. When I returned home after a long journey, "
        "I found a letter on the kitchen table. My sister had left it there "
        "before she went to the station. She asked me to bring her blue "
        "bag because she had forgotten it. I read the letter and called her "
        "to say I would arrive before the evening train."
        for number in range(1001, 1101)
    )
