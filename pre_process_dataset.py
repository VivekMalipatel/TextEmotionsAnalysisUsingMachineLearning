import pandas as pd
import string
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import re

# Download necessary NLTK data
nltk.download('omw-1.4')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')

# Initialize the WordNet Lemmatizer
lemmatizer = WordNetLemmatizer()

# Define the dictionary for contractions
contractions_dict = {
    "ive": "I have",
    "im": "I am",
    "youre": "you are",
    "were": "we are",
    "theyre": "they are",
    "cant": "cannot",
    "couldnt": "could not",
    "dont": "do not",
    "doesnt": "does not",
    "its": "it is",
    "thats": "that is",
    "theres": "there is",
    # Add more contractions as needed
}

# Regular expression for finding contractions
contractions_re = re.compile('(%s)' % '|'.join(contractions_dict.keys()))

def expand_contractions(text, contractions_dict=contractions_dict):
    def replace(match):
        return contractions_dict[match.group(0)]
    return contractions_re.sub(replace, text)

# Function to convert NLTK's part of speech tags to wordnet tags
def nltk_pos_to_wordnet_pos(nltk_pos):
    if nltk_pos.startswith('J'):
        return wordnet.ADJ
    elif nltk_pos.startswith('V'):
        return wordnet.VERB
    elif nltk_pos.startswith('N'):
        return wordnet.NOUN
    elif nltk_pos.startswith('R'):
        return wordnet.ADV
    else:
        return None

# Function to clean, lemmatize, and retain text as sentences
def clean_and_lemmatize(text):

    text = expand_contractions(text)
    # Convert text to lowercase
    text = text.lower()
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Tokenize text
    tokens = text.split()
    # Part of speech tagging
    nltk_pos_tags = nltk.pos_tag(tokens)
    # Lemmatization
    lemmatized_tokens = []
    for word, tag in nltk_pos_tags:
        wordnet_pos = nltk_pos_to_wordnet_pos(tag)
        if wordnet_pos is None:
            lemmatized_tokens.append(word)
        else:
            lemmatized_tokens.append(lemmatizer.lemmatize(word, wordnet_pos))
    # Joining tokens back into a cleaned sentence
    cleaned_sentence = ' '.join(lemmatized_tokens)
    return cleaned_sentence

def main():
    # Load the dataset
    data_path = 'text.csv'
    data = pd.read_csv(data_path)

    # Drop the unnecessary index column
    if 'Unnamed: 0' in data.columns:
        data.drop(columns=['Unnamed: 0'], inplace=True)

    # Describe the dataset
    print("Dataset Overview:")
    print(data.describe())
    print("\nFirst 5 rows of the dataset:")
    print(data.head())

    # Apply cleaning and lemmatization to the text data
    data['text'] = data['text'].apply(clean_and_lemmatize)

    print("\nAfter Pre-processing and Lemmatization:")
    print(data.head())

    data.to_csv('pre_processed_text.csv',index=False)

if __name__ == '__main__':
    main()
