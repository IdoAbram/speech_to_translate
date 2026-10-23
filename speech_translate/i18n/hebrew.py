"""Hebrew interface text, keyed by the English message templates.

Plural imperatives (for example "נסה") keep the text gender-neutral.
Placeholders in braces must match the English template exactly.
"""

MESSAGES = {
    # Top bar and screens.
    "Full screen": "מסך מלא",
    "Settings": "הגדרות",
    "Exit": "יציאה",
    "Choose a song": "בחירת שיר",
    "Click here to choose a song file (MP3)": (
        "לחץ כאן כדי לבחור קובץ שיר (MP3)"
    ),
    "or drag the file here": "או גרור את הקובץ לכאן",
    "MP3 songs (*.mp3)": "שירים בפורמט MP3 (*.mp3)",
    "The chosen song:": "השיר שנבחר:",
    "Another song": "שיר אחר",
    "The song is in": "השיר בשפה",
    "Translate into": "לתרגם ל־",
    "Translate": "לתרגם",
    "+ New song": "+ שיר חדש",
    "Please choose an MP3 file.": "יש לבחור קובץ MP3.",
    "Processing failed: {error}": "משהו השתבש: {error}",
    # Working screen.
    "Reading the song": "קורא את השיר",
    "Hearing the words": "שומע את המילים",
    "Translating": "מתרגם",
    "Reading the song…": "קורא את השיר…",
    "Hearing the words…": "שומע את המילים…",
    "Translating…": "מתרגם…",
    "You can wait calmly; this takes about a minute.": (
        "אפשר לחכות בנחת, זה לוקח בערך דקה."
    ),
    "{elapsed} so far": "עברו {elapsed}",
    "Cancel": "ביטול",
    # Lyrics screen.
    "Song words · {language}": "מילות השיר · {language}",
    "Translation · {language}": "תרגום · {language}",
    "You can fix a misheard word here.": ("אפשר לתקן כאן מילה שנשמעה לא נכון."),
    "Copy": "העתקה",
    "You can change words in the translation too.": (
        "אפשר לשנות כאן גם מילים בתרגום."
    ),
    "The whole translation was copied.": "כל התרגום הועתק.",
    "The song words were copied.": "מילות השיר הועתקו.",
    "The words changed. Click Translate to translate again.": (
        'המילים השתנו. לחץ על "לתרגם" כדי לתרגם שוב.'
    ),
    # Saving.
    "Save…": "שמירה…",
    "Save text": "שמירת טקסט",
    "Text files (*.txt)": "קובצי טקסט (*.txt)",
    "Saved {name}": "נשמר: {name}",
    "Could not save: {error}": "השמירה נכשלה: {error}",
    # Settings and online translation.
    "Better translation over the internet": "תרגום משופר באינטרנט",
    "When the computer is connected to the internet, the translation "
    "understands slang and expressions much better. Without internet, the "
    "translation is done on this computer, and that always works.": (
        "כשהמחשב מחובר לאינטרנט, התרגום מבין סלנג וביטויים הרבה יותר טוב. "
        "בלי אינטרנט, התרגום נעשה במחשב, וזה עובד תמיד."
    ),
    "Groq key: saved ✓": "מפתח Groq: שמור ✓",
    "On": "פועל",
    "Off": "כבוי",
    "No Groq key yet": "עדיין אין מפתח Groq",
    "Change key…": "החלפת מפתח…",
    "Display": "תצוגה",
    "Full screen / window": "מסך מלא / חלון",
    "Close": "סגירה",
    "Online translation": "תרגום באינטרנט",
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
        "הדבק כאן את המפתח (הוא מתחיל ב-gsk_)"
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
        "זוהו מילים עד {done} מתוך {total} · ממשיך לקטע הבא…"
    ),
    "Identifying the song language…": "מזהה את שפת השיר…",
    "Detected language '{code}'. Open Settings to choose English, Hebrew, "
    "or Polish if this detection is incorrect.": (
        "זוהתה שפה לא נתמכת ('{code}'). אם הזיהוי שגוי, פתח את ההגדרות "
        "ובחר אנגלית, עברית או פולנית."
    ),
    "Detected {name}. Transcribing…": "זוהתה {name}. מזהה את המילים…",
    "Choose an existing MP3 file.": "יש לבחור קובץ MP3 קיים.",
    "This audio file is empty.": "קובץ השמע ריק.",
    "Loading the speech model…": "טוען את מודל זיהוי הדיבור…",
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
    "Reading the audio file…": "קורא את קובץ השמע…",
    "No vocals were found. Try a clearer recording.": (
        "לא נמצאה שירה. נסה הקלטה ברורה יותר."
    ),
    "Transcribing audio · Waiting for the first passage…": (
        "מזהה את המילים · ממתין לקטע הראשון…"
    ),
    # Offline translation.
    "The decoder needs a smaller passage.": "המודל צריך קטע קצר יותר.",
    "A line could not be translated. Try editing it.": (
        "לא ניתן היה לתרגם שורה. נסה לערוך אותה."
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
    "Loading the translation model…": "טוען את מודל התרגום…",
    "Translating passage 1 of {total}…": "מתרגם קטע 1 מתוך {total}…",
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
        "התרגום באינטרנט לא זמין. מתרגם במחשב…"
    ),
    # Online translation with Groq.
    "Paste the whole Groq key, without spaces.": (
        "הדבק את כל המפתח, בלי רווחים."
    ),
    "Groq's free daily limit was reached. Try again later.": (
        "המכסה היומית החינמית נגמרה. נסה שוב מחר."
    ),
    "Groq could not be reached. Check the internet connection.": (
        "אין חיבור לתרגום באינטרנט. בדוק את החיבור לאינטרנט."
    ),
    "Groq returned an unreadable answer.": "התקבלה תשובה לא תקינה.",
    "Groq returned no translation. Try again.": "לא התקבל תרגום. נסה שוב.",
    "Translating with Groq: part {part} of {total}…": (
        "מתרגם באינטרנט: חלק {part} מתוך {total}…"
    ),
    "Groq could not return the song line by line. Try again.": (
        "לא התקבל תרגום שורה אחר שורה. נסה שוב."
    ),
    "Groq free limit: waiting {seconds} s…": (
        "הגעת למכסה החינמית: ממתין {seconds} שניות…"
    ),
    "Groq's free limit was reached. Wait a minute and try again.": (
        "הגעת למכסה החינמית. חכה דקה ונסה שוב."
    ),
    "Groq rejected the key. Check it under Online translation.": (
        "המפתח לא התקבל. בדוק אותו בהגדרות, תחת תרגום באינטרנט."
    ),
    "This Groq model is not available. Check GROQ_MODEL.": (
        "מודל התרגום באינטרנט לא זמין. בדוק את GROQ_MODEL."
    ),
    "Groq rejected the request. Try another GROQ_MODEL.": (
        "הבקשה לא התקבלה. נסה GROQ_MODEL אחר."
    ),
    "Groq failed with HTTP error {status}. Try again later.": (
        "התרגום באינטרנט נכשל (שגיאה {status}). נסה שוב מאוחר יותר."
    ),
}
