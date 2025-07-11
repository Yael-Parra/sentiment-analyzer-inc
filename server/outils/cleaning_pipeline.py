import pandas as pd
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline
from tqdm import tqdm

# Initialize sentiment analysis tools once
analyzer_en = SentimentIntensityAnalyzer()
tqdm.pandas()

# ---------------------------------------------------------------
# Normalize column names
def normalize_column_names(df):
    """
    Standardize column names to lowercase with underscores as word separators.
    """
    df.columns = (
        df.columns
        .str.replace(r'(?<!^)(?=[A-Z])', '_', regex=True)  # Insert underscore before each uppercase (except start)
        .str.lower()                                       # Convert all to lowercase
        .str.strip()                                       # Remove leading and trailing spaces
    )
    return df

# ----------------------------------------------------------------
# Handle duplicate rows
def handle_duplicates(df):
    """
    Handle duplicate rows in the dataset with multiple strategies:
    1. Remove exact duplicates across all columns
    2. Ensure each comment_id is unique
    3. Remove likely duplicates (same author, text, and timestamp)
    """
    df_clean = df.copy()
    
    # First, identify exact duplicates across all columns
    df_clean = df_clean.drop_duplicates()
    
    # Ensure each comment_id is unique
    if 'comment_id' in df_clean.columns:
        df_clean = df_clean.drop_duplicates(subset=['comment_id'], keep='first')
    
    # Remove likely duplicates (same author, text, and timestamp)
    duplicate_cols = ['author', 'text', 'published_at_comment']
    if all(col in df_clean.columns for col in duplicate_cols):
        df_clean = df_clean.drop_duplicates(subset=duplicate_cols, keep='first')
    
    return df_clean

# ----------------------------------------------------------------
# Handle null values
def handle_nulls(df):
    """
    Handle null values with column-specific strategies:
    - Drop rows with null IDs
    - Fill author info with 'unknown'
    - Assume False for missing boolean flags
    - Fill engagement metrics with 0
    - Special handling for timestamps
    """
    df_clean = df.copy()

    null_handling_strategies = {
        # IDs - must exist, drop rows if null
        'thread_id': {'action': 'drop'},
        'comment_id': {'action': 'drop'},
        'video_id': {'action': 'drop'},

        # Author info - fill with 'unknown', but track frequency externally
        'author': {'action': 'fill', 'value': 'unknown'},
        'author_channel_id': {'action': 'fill', 'value': 'unknown'},

        # Boolean flag - assume False if missing, but validate assumption
        'is_reply': {'action': 'fill', 'value': False},

        # Parent comment ID - missing means no reply, leave as is
        'parent_comment_id': {'action': 'leave'},

        # Timestamp - drop if missing values are few, otherwise impute and flag
        'published_at_comment': {'action': 'conditional_drop', 'threshold': 0.05},

        # Text - no text means no analysis, drop such rows
        'text': {'action': 'drop'},

        # Engagement metrics - fill missing values with zero
        'like_count_comment': {'action': 'fill', 'value': 0},
        'reply_count': {'action': 'fill', 'value': 0}
    }

    for column, strategy in null_handling_strategies.items():
        if column not in df_clean.columns:
            continue

        action = strategy['action']
        if action == 'drop':
            # Drop rows where this column is null
            df_clean = df_clean.dropna(subset=[column])
        elif action == 'fill':
            # Fill nulls with specified value
            df_clean[column] = df_clean[column].fillna(strategy['value'])
        elif action == 'leave':
            # Do nothing for this column
            continue
        elif action == 'conditional_drop':
            # Calculate ratio of nulls in this column
            null_ratio = df_clean[column].isna().mean()
            threshold = strategy.get('threshold', 0)
            if null_ratio <= threshold:
                # If nulls are under threshold, drop those rows
                df_clean = df_clean.dropna(subset=[column])
            else:
                # If many nulls, fill with a placeholder and add a flag column
                fill_value = pd.Timestamp('1970-01-01')  # placeholder date
                df_clean[column + '_was_null'] = df_clean[column].isna()
                df_clean[column] = df_clean[column].fillna(fill_value)

    return df_clean

# ----------------------------------------------------------------
# Convert data types
def convert_data_types(df):
    """
    Convert columns to appropriate data types with error handling.
    """
    df_copy = df.copy()
    
    conversions = {
        'published_at_comment': lambda col: pd.to_datetime(col, errors='coerce'),
        'like_count_comment': 'int',
        'reply_count': 'int',
        'is_reply': 'bool',
        'author_channel_id': 'string'
    }
    
    for col, conversion in conversions.items():
        if col not in df_copy.columns:
            continue
        try:
            if callable(conversion):
                df_copy[col] = conversion(df_copy[col])
            else:
                df_copy[col] = df_copy[col].astype(conversion)
        except Exception as e:
            print(f"Warning: Could not convert column '{col}': {e}")
    
    return df_copy
# ----------------------------------------------------------------
# URL handling functions
def extract_and_remove_urls(df, text_column='text'):
    """
    1. Extracts URLs to new column 'extracted_urls' (as lists)
    2. Removes URLs from original text column
    3. Adds 'has_url' boolean flag
    """
    df = df.copy()
    
    # Extract URLs (store as list)
    df['extracted_urls'] = df[text_column].apply(lambda x: re.findall(r'https?://\S+|www\.\S+', str(x)))
    
    # Remove URLs from text (keep everything else)
    df[text_column] = df[text_column].apply(lambda x: re.sub(r'https?://\S+|www\.\S+', '', str(x)))
    
    # Add simple boolean flag
    df['has_url'] = df['extracted_urls'].apply(lambda x: len(x) > 0)
    
    return df

# ----------------------------------------------------------------
# Self-promotion detection
self_promo_keywords = {
    # English
    'en': [
        'check out my', 'subscribe to', 'follow me', 'visit my', 'link in bio',
        'watch my', 'support my', 'my channel', 'my content', 'please subscribe',
        'giveaway on my', 'join my', 'don’t forget to follow', 'my new video',
        'check my', 'like and subscribe', 'hit subscribe', 'sub to my',
        'drop a sub', 'my latest video', 'my socials', 'follow my', 'my page',
        'my profile', 'my website', 'my blog', 'my podcast', 'my merch'
    ],
    
    # Spanish
    'es': [
        'mira mi', 'suscríbete a', 'suscribete a','sígueme', 'sigueme', 'visita mi', 'enlace en bio',
        've mi', 'apoya mi', 'mi canal', 'mi contenido', 'por favor suscríbete',
        'sorteo en mi', 'únete a mi', 'no olvides seguir', 'mi nuevo video',
        'checa mi', 'dale like y suscríbete', 'suscribete', 'mis redes'
    ],
    
    # Hindi
    'hi': [
        'मेरा चैनल देखो', 'सब्सक्राइब करो', 'मुझे फॉलो करो', 'मेरी वेबसाइट देखो',
        'मेरा लिंक', 'मेरा वीडियो देखो', 'मेरे चैनल को सपोर्ट करो', 'मेरा कंटेंट',
        'कृपया सब्सक्राइब करें', 'मेरे चैनल से जुड़ें', 'मेरा नया वीडियो'
    ],
    
    # Portuguese
    'pt': [
        'confira meu', 'inscreva-se no', 'me siga', 'visite meu', 'link na bio',
        'assista meu', 'apoie meu', 'meu canal', 'meu conteúdo', 'por favor se inscreva',
        'sorteio no meu', 'junte-se ao meu', 'não esqueça de seguir'
    ],
    
    # French
    'fr': [
        'regarde mon', 'abonne-toi à', 'suis-moi', 'visite mon', 'lien en bio',
        'regarde ma', 'soutiens mon', 'ma chaîne', 'mon contenu', 'abonne-toi s\'il te plaît',
        'concours sur mon', 'rejoins mon', 'n\'oublie pas de suivre'
    ],
    
    # German
    'de': [
        'schau dir mein', 'abonniere', 'folge mir', 'besuche mein', 'link in bio',
        'sieh dir mein', 'unterstütze mein', 'mein kanal', 'mein inhalt', 'bitte abonnieren',
        'gewinnspiel auf mein', 'tritt mein bei', 'vergiss nicht zu folgen'
    ],
    
    # Russian
    'ru': [
        'посмотри мой', 'подпишись на', 'подпишись на меня', 'зайди на мой', 'ссылка в профиле',
        'посмотри мое', 'поддержи мой', 'мой канал', 'мой контент', 'пожалуйста подпишись',
        'конкурс на моем', 'присоединяйся к моему', 'не забудь подписаться'
    ],
    
    # Japanese
    'ja': [
        '私のチャンネルを見て', '登録して', 'フォローして', '私のサイトを見て',
        'プロフィールのリンク', '私の動画を見て', '私のチャンネルをサポートして', '私のコンテンツ',
        'チャンネル登録お願いします', '私の新しい動画'
    ],
    
    # Arabic
    'ar': [
        'شاهد قناتي', 'اشترك في', 'تابعني', 'زور موقعي', 'الرابط في البايو',
        'ادعم قناتي', 'قناتي', 'محتواي', 'من فضلك اشترك', 'انضم إلى قناتي',
        'لا تنسى المتابعة'
    ]
}


def is_self_promotional(text):
    """Detect if text contains self-promotional content."""
    if not isinstance(text, str):
        return False
        
    text = text.lower()
    # Check all languages
    for lang_keywords in self_promo_keywords.values():
        if any(phrase in text for phrase in lang_keywords):
            return True
    return False
# ----------------------------------------------------------------
def detect_tags(df, text_column='text'):
    """Add a boolean column indicating if there are @tags and clean them from the text column."""
    
    def has_tag(text):
        if not isinstance(text, str):
            return False
        return bool(re.search(r'@\w+', text))
    
    def remove_tags(text):
        if not isinstance(text, str):
            return text
        return re.sub(r'@\w+', '', text).strip()
    
    df['has_tag'] = df[text_column].apply(has_tag)
    df[text_column] = df[text_column].apply(remove_tags)
    
    return df
# ----------------------------------------------------------------
# Removing line breaks and extra spaces
def remove_linebreaks_and_spaces(df, text_columns=['text']):
    """
    Remove line breaks and extra spaces from specified text columns.
    """
    df_clean = df.copy()
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = (
                df_clean[col]
                .astype(str)
                .str.replace(r'[\r\n]+', ' ', regex=True)  # Replace line breaks
                .str.strip()  # Trim leading/trailing whitespace
                .str.replace(r'\s{2,}', ' ', regex=True)  # Collapse multiple spaces
            )
    return df_clean

# ----------------------------------------------------------------
# Sentiment analysis
def analyze_sentiment(text):
    if not isinstance(text, str) or not text.strip():
        return pd.Series({
            'sentiment_type': 'neutral',
            'sentiment_score': 0.0,
            'sentiment_intensity': 'weak'
        })

    scores = analyzer_en.polarity_scores(text)
    compound = scores['compound']
    
    # Sentiment type
    if compound >= 0.05:
        sentiment_type = 'positive'
    elif compound <= -0.05:
        sentiment_type = 'negative'
    else:
        sentiment_type = 'neutral'
    
    sentiment_score = float(compound)
    # Sentiment intensity, lo tuve que cambiar a float para las estadísticas
    abs_score = abs(compound)
    if abs_score >= 0.6:
        sentiment_intensity = 'strong'
    elif abs_score >= 0.3:
        sentiment_intensity = 'moderate'
    else:
        sentiment_intensity = 'weak'
    
    return pd.Series({
        'sentiment_type': sentiment_type,
        'sentiment_score': sentiment_score,
        'sentiment_intensity': sentiment_intensity
    })

# ----------------------------------------------------------------
# Main pipeline function by order of operations
def clean_youtube_data(df):
# Step 1  normalize_column_names
    df = normalize_column_names(df)
# Step 2  handle_duplicates
    df = handle_duplicates(df)
# Step 3  handle_nulls
    df = handle_nulls(df)
# Step 4  convert_data_types
    df = convert_data_types(df)
# Step 5  extract_and_remove_urls
    df = extract_and_remove_urls(df)
# Step 6  is_self_promotional
    df['is_self_promotional'] = df['text'].apply(is_self_promotional)
# Step 7  detect_tags
    df = detect_tags(df)
# Step 8  remove_linebreaks_and_spaces
    df = remove_linebreaks_and_spaces(df)
# Step 9 analyze_sentiment
    df[['sentiment_type', 'sentiment_score', 'sentiment_intensity']] = df['text'].apply(analyze_sentiment)

    return df

# ----------------------------------------------------------------
def process_youtube_comments(input_df: pd.DataFrame) -> pd.DataFrame:
    return clean_youtube_data(input_df)