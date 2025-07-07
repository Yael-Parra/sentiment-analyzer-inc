import pandas as pd
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline
from tqdm import tqdm

# Initialize sentiment analysis tools once
classifier_es_sentiment = pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")
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
# Clean text content
def clean_text_content(df, text_columns=['text']):
    """
    Clean text content by:
    - Removing line breaks and extra spaces
    - Removing URLs (while extracting them to a separate column)
    - Adding self-promotion detection
    - Adding tag detection
    """
    df_clean = df.copy()
    
    # Remove line breaks and extra spaces
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].str.replace(r'[\r\n]+', ' ', regex=True).str.strip()
    
    # Extract and remove URLs
    if 'text' in df_clean.columns:
        df_clean = extract_and_remove_urls(df_clean)
    
    # Add self-promotion detection
    df_clean['is_self_promotional'] = df_clean['text'].apply(is_self_promotional)
    
    # Add tag detection
    df_clean['contains_tag'] = df_clean['text'].apply(contains_tag)
    
    return df_clean

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
    df['extracted_urls'] = df[text_column].apply(
        lambda x: re.findall(r'https?://\S+|www\.\S+', str(x))
    
    # Remove URLs from text (keep everything else)
    df[text_column] = df[text_column].apply(
        lambda x: re.sub(r'https?://\S+|www\.\S+', '', str(x))
    )
    
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
        'giveaway on my', 'join my', 'don't forget to follow', 'my new video',
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
    
    # Other languages remain the same...
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

def contains_tag(text):
    """Detect if text contains @ tags."""
    if not isinstance(text, str):
        return False
    return '@' in text

# ----------------------------------------------------------------
# Sentiment analysis
def analyze_sentiment(df, text_column='text'):
    """
    Perform multilingual sentiment analysis on text content.
    Returns DataFrame with added sentiment columns.
    """
    def get_sentiment(text):
        if not isinstance(text, str) or not text.strip():
            return {'sentiment_type': 'neutral', 'sentiment_intensity': 'weak'}
        
        is_spanish = any(ord(c) > 128 for c in text)
        
        if is_spanish:
            results = classifier_es_sentiment(text, truncation=True, max_length=512)
            result_dict = {r['label'].lower(): r['score'] for r in results}
            prob_pos = result_dict.get('pos', 0)
            prob_neg = result_dict.get('neg', 0)
            prob_neu = result_dict.get('neu', 0)
            compound = prob_pos - prob_neg
            
            if compound >= 0.05:
                sentiment = 'positive'
            elif compound <= -0.05:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            abs_compound = abs(compound)
            
        else:
            scores = analyzer_en.polarity_scores(text)
            compound = scores['compound']
            if compound >= 0.05:
                sentiment = 'positive'
            elif compound <= -0.05:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            abs_compound = abs(compound)
        
        if abs_compound > 0.5:
            intensity = 'strong'
        elif abs_compound > 0.2:
            intensity = 'moderate'
        else:
            intensity = 'weak'
        
        return {
            'sentiment_type': sentiment,
            'sentiment_intensity': intensity,
        }
    
    sentiment_df = df[text_column].progress_apply(get_sentiment).apply(pd.Series)
    return pd.concat([df, sentiment_df], axis=1)

# ----------------------------------------------------------------
# Main pipeline function
def clean_youtube_data(df):
    """
    Complete cleaning pipeline for YouTube comments data.
    Processes the DataFrame through all cleaning steps in proper order.
    """
    # Step 1: Normalize column names
    df_clean = normalize_column_names(df)
    
    # Step 2: Handle duplicates
    df_clean = handle_duplicates(df_clean)
    
    # Step 3: Handle null values
    df_clean = handle_nulls(df_clean)
    
    # Step 4: Convert data types
    df_clean = convert_data_types(df_clean)
    
    # Step 5: Clean text content
    df_clean = clean_text_content(df_clean)
    
    # Step 6: Analyze sentiment (optional - can be commented out if not needed)
    df_clean = analyze_sentiment(df_clean)
    
    return df_clean

# ----------------------------------------------------------------
if __name__ == "__main__":
   
    df = pd.read_csv('AQUI TIENE QUE ESTAR EL PATH O EL DF QUE GENERA YOUTUBE_EXTRACT DENTRO DE LA CARPETA ETL')
    
    # Example with dummy data
    data = {
        'commentId': ['1', '2', '3'],
        'Author': ['user1', 'user2', None],
        'Text': ['Great video!', 'Check out my channel', None],
        'PublishedAt': ['2023-01-01', '2023-01-02', None],
        'LikeCount': ['10', None, '5']
    }
    df = pd.DataFrame(data)
    
    # Run the cleaning pipeline
    cleaned_df = clean_youtube_data(df)
    
    print("Original shape:", df.shape)
    print("Cleaned shape:", cleaned_df.shape)
    print("Cleaned columns:", cleaned_df.columns.tolist())

