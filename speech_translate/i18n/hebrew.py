"""Hebrew interface text, keyed by the English message templates.

Plural imperatives (for example "נסו") keep the text gender-neutral.
Placeholders in braces must match the English template exactly.
"""

MESSAGES = {
    # Main screen.
    "Settings": "הגדרות",
    "Exit": "יציאה",
    "Every song has a story.": "לכל שיר יש סיפור.",
    "Choose a song, check its words, and translate them.": (
        "בוחרים שיר, בודקים את המילים, ומתרגמים."
    ),
    "1. Choose a song": "1. בחירת שיר",
    "2. Translate into": "2. תרגום לשפה",
    "Click here to choose a song (MP3)": "לחצו כאן כדי לבחור שיר (MP3)",
    "Choose a song": "בחירת שיר",
    "MP3 songs (*.mp3)": "שירים בפורמט MP3 (*.mp3)",
    "{name} · click to choose another song": (
        "{name} · לחצו כדי לבחור שיר אחר"
    ),
    "Song words": "מילות השיר",
    "Translation": "תרגום",
    "Song language: {name}": "שפת השיר: {name}",
    "Song language: {name} (check in Settings)": (
        "שפת השיר: {name} (כדאי לבדוק בהגדרות)"
    ),
    "Choose a song to begin.": "בחרו שיר כדי להתחיל.",
    "Loading…": "טוען…",
    "Cancel": "ביטול",
    "Cancelling after the current step…": "מבטלים בסוף השלב הנוכחי…",
    "Working · {elapsed}": "עובדים על זה · {elapsed}",
    "Working · {percent}% · {elapsed}": "עובדים על זה · {percent}% · {elapsed}",
    "Please choose an MP3 file.": "יש לבחור קובץ MP3.",
    "There are no words to translate yet.": "עדיין אין מילים לתרגום.",
    "Words ready. Fix any mistakes, then choose a language.": (
        "המילים מוכנות. תקנו טעויות אם יש, ואז בחרו שפה."
    ),
    "Translation ready. Line numbers match the song's lines.": (
        "התרגום מוכן. מספרי השורות תואמים לשורות השיר."
    ),
    "Processing failed: {error}": "משהו השתבש: {error}",
    # Copy and save.
    "Copy": "העתקה",
    "Save…": "שמירה…",
    "Save text": "שמירת טקסט",
    "Text files (*.txt)": "קובצי טקסט (*.txt)",
    "There is no text to save yet.": "עדיין אין טקסט לשמירה.",
    "Saved {name}": "נשמר: {name}",
    "Could not save: {error}": "השמירה נכשלה: {error}",
    # Settings and online translation.
    "Song language": "שפת השיר",
    "Detect automatically": "זיהוי אוטומטי",
    "If the words came out in the wrong language, choose the song's "
    "language here. The song is read again.": (
        "אם המילים יצאו בשפה הלא נכונה, בחרו כאן את שפת השיר. השיר ייקרא מחדש."
    ),
    "Online translation": "תרגום באינטרנט",
    "Change…": "שינוי…",
    "On: better translation over the internet": (
        "פועל: תרגום טוב יותר דרך האינטרנט"
    ),
    "Off: translation on this computer only": "כבוי: תרגום במחשב הזה בלבד",
    "Window / full screen": "חלון / מסך מלא",
    "Close": "סגירה",
    "Online translation is on.": "התרגום באינטרנט פועל.",
    "Online translation is off.": "התרגום באינטרנט כבוי.",
    "Online translation (Groq) understands slang and idioms much better. "
    "Get a free key (no card needed) at {link} and paste it below. When you "
    "translate, the lyrics are sent to Groq. Without internet, the "
    "translation is done on this computer.": (
        "התרגום באינטרנט (Groq) מבין סלנג וביטויים הרבה יותר טוב. "
        "אפשר לקבל מפתח בחינם (בלי כרטיס אשראי) באתר {link} ולהדביק אותו "
        "כאן. בזמן התרגום, מילות השיר נשלחות ל-Groq. בלי אינטרנט, "
        "התרגום נעשה במחשב."
    ),
    "Paste the key here (it starts with gsk_)": (
        "הדביקו כאן את המפתח (הוא מתחיל ב-gsk_)"
    ),
    "Turn off": "כיבוי",
    "Save": "שמירה",
    "The key could not be removed: {error}": "לא ניתן למחוק את המפתח: {error}",
    # Languages.
    "English": "אנגלית",
    "Hebrew": "עברית",
    "Polish": "פולנית",
    "Choose English, Hebrew, or Polish.": "יש לבחור אנגלית, עברית או פולנית.",
    # Speech recognition.
    "Cancelled. Your completed transcript is kept.": (
        "בוטל. מילות השיר שכבר זוהו נשמרו."
    ),
    "Audio transcribed: {done} / {total} · Processing the next passage…": (
        "זוהו מילים עד {done} מתוך {total} · ממשיכים לקטע הבא…"
    ),
    "Identifying the song language…": "מזהים את שפת השיר…",
    "Detected language '{code}'. Open Settings to choose English, Hebrew, "
    "or Polish if this detection is incorrect.": (
        "זוהתה שפה לא נתמכת ('{code}'). אם הזיהוי שגוי, פתחו את ההגדרות "
        "ובחרו אנגלית, עברית או פולנית."
    ),
    "Detected {name}. Transcribing…": "זוהתה {name}. מזהים את המילים…",
    "Choose an existing MP3 file.": "יש לבחור קובץ MP3 קיים.",
    "This audio file is empty.": "קובץ השמע ריק.",
    "Loading the speech model…": "טוענים את מודל זיהוי הדיבור…",
    "Transcript ready.": "מילות השיר מוכנות.",
    "Could not read the audio: {error}": "לא ניתן לקרוא את קובץ השמע: {error}",
    "No vocals were found. This recording is silent.": (
        "לא נמצאה שירה. ההקלטה שקטה."
    ),
    "Choose a base, small, or medium speech model.": (
        "יש לבחור מודל דיבור base, small או medium."
    ),
    "Missing {size} model. Run python setup_models.py --speech-model {size} "
    "on a connected computer first.": (
        "מודל {size} חסר. יש להריץ python setup_models.py "
        "--speech-model {size} במחשב שמחובר לאינטרנט."
    ),
    "Reading the audio file…": "קוראים את קובץ השמע…",
    "No vocals were found. Try a clearer recording.": (
        "לא נמצאה שירה. נסו הקלטה ברורה יותר."
    ),
    "Transcribing audio · Waiting for the first passage…": (
        "מזהים את המילים · ממתינים לקטע הראשון…"
    ),
    # Offline translation.
    "The decoder needs a smaller passage.": "המודל צריך קטע קצר יותר.",
    "A line could not be translated. Try editing it.": (
        "לא ניתן היה לתרגם שורה. נסו לערוך אותה."
    ),
    "A numeric identifier was omitted.": "מספר הושמט בתרגום.",
    "The model could not finish this passage.": (
        "המודל לא הצליח לסיים את הקטע הזה."
    ),
    "A text fragment exceeds the model limit.": (
        "קטע טקסט ארוך מדי עבור המודל."
    ),
    "The upgraded translation model is missing. Run setup_models.py on a "
    "connected computer, or copy the complete models folder.": (
        "מודל התרגום חסר. יש להריץ setup_models.py במחשב שמחובר לאינטרנט, "
        "או להעתיק את תיקיית models המלאה."
    ),
    "Transcribe a song or enter some text first.": (
        "קודם צריך לבחור שיר או להקליד מילים."
    ),
    "Loading the translation model…": "טוענים את מודל התרגום…",
    "Translating passage 1 of {total}…": "מתרגמים קטע 1 מתוך {total}…",
    "Translated {done} of {total} passages…": (
        "תורגמו {done} מתוך {total} קטעים…"
    ),
    "Translation ready.": "התרגום מוכן.",
    "Groq was unavailable ({error}) Used the offline model, which "
    "translates more literally.": (
        "התרגום באינטרנט לא היה זמין ({error}). התרגום נעשה במחשב, "
        "ולכן הוא מילולי יותר."
    ),
    "Groq unavailable. Using the offline model…": (
        "התרגום באינטרנט לא זמין. מתרגמים במחשב…"
    ),
    # Online translation with Groq.
    "Paste the whole Groq key, without spaces.": (
        "הדביקו את כל המפתח, בלי רווחים."
    ),
    "Groq's free daily limit was reached. Try again later.": (
        "המכסה היומית החינמית נגמרה. נסו שוב מחר."
    ),
    "Groq could not be reached. Check the internet connection.": (
        "אין חיבור לתרגום באינטרנט. בדקו את החיבור לאינטרנט."
    ),
    "Groq returned an unreadable answer.": "התקבלה תשובה לא תקינה.",
    "Groq returned no translation. Try again.": "לא התקבל תרגום. נסו שוב.",
    "Translating with Groq: part {part} of {total}…": (
        "מתרגמים באינטרנט: חלק {part} מתוך {total}…"
    ),
    "Groq could not return the song line by line. Try again.": (
        "לא התקבל תרגום שורה אחר שורה. נסו שוב."
    ),
    "Groq free limit: waiting {seconds} s…": (
        "הגעתם למכסה החינמית: ממתינים {seconds} שניות…"
    ),
    "Groq's free limit was reached. Wait a minute and try again.": (
        "הגעתם למכסה החינמית. חכו דקה ונסו שוב."
    ),
    "Groq rejected the key. Check it under Online translation.": (
        "המפתח לא התקבל. בדקו אותו בהגדרות, תחת תרגום באינטרנט."
    ),
    "This Groq model is not available. Check GROQ_MODEL.": (
        "מודל התרגום באינטרנט לא זמין. בדקו את GROQ_MODEL."
    ),
    "Groq rejected the request. Try another GROQ_MODEL.": (
        "הבקשה לא התקבלה. נסו GROQ_MODEL אחר."
    ),
    "Groq failed with HTTP error {status}. Try again later.": (
        "התרגום באינטרנט נכשל (שגיאה {status}). נסו שוב מאוחר יותר."
    ),
}
