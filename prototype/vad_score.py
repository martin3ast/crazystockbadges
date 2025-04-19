#!env python 
import pandas as pd
import numpy as np
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk import download
import os
import pdb


# Paper: From a Large Language Model to Three-Dimensional Sentiment⋆

# Download necessary NLTK data
download('punkt')
download('punkt_tab')
download('stopwords')

# Load the NRC VAD lexicon
vad_lexicon = pd.read_csv('./NRC-VAD-Lexicon/NRC-VAD-Lexicon.txt', sep='\t', names=['Valence','Arousal','Dominane'])
# Hedging words indicating uncertainty
hedging_words = {'possibly', 'might', 'could', 'maybe', 'perhaps', 'seems', 'appears', 'likely', 'unlikely'}

f = open('./stock_report')

stock_report = f.read()

# Function to calculate VAC scores
def calculate_vac(text):
    words = word_tokenize(text.lower())
    valence_scores = []
    arousal_scores = []
    hedging_count = 0
    total_words = 0
    
    for word in words:
        if word.isalpha() and word not in stopwords.words('english'):
            total_words += 1
            if word in vad_lexicon.index:
                valence = vad_lexicon.loc[word]['Valence']
                arousal = vad_lexicon.loc[word]['Arousal']
                valence_scores.append(valence)
                arousal_scores.append(arousal)
            if word in hedging_words:
                hedging_count += 1
    
    avg_valence = np.mean(valence_scores) if valence_scores else 0
    avg_arousal = np.mean(arousal_scores) if arousal_scores else 0
    confidence = 1 - (hedging_count / total_words) if total_words else 1
    
    return avg_valence, avg_arousal, confidence

# Calculate VAC scores 
valence, arousal, confidence = calculate_vac(stock_report)

print(stock_report)
print(f'Valence={valence} Arousal={arousal} Confidence={confidence}')
