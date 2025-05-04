#!/usr/bin/env python3
"""
Improved Sentiment Analysis Module for Crazy Stock Badges Project

This class provides enhanced sentiment analysis capabilities for analyzing
stock reports and extracting emotional dimensions using the NRC VAD lexicon.

Version 1.0 - Cline implementation for Martin East - Based on original requirements for sentiment analysis of stock reports - Apr 13, 2025.
"""

import os
import pandas as pd
import numpy as np
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk import download
import logging
from pathlib import Path
import re
import json
from collections import Counter

# Get logger
logger = logging.getLogger('improved_sentiment')

# Default paths
DEFAULT_LEXICON_PATH = './NRC-VAD-Lexicon/NRC-VAD-Lexicon.txt'
DEFAULT_REPORT_PATH = './stock_report'

# Ensure NLTK data is available
from nltk.data import find

# Check for punkt
try:
    find('tokenizers/punkt')
    logger.info("NLTK punkt tokenizer found locally")
except LookupError:
    logger.info("NLTK punkt tokenizer not found locally, downloading...")
    download('punkt', quiet=True)
    logger.info("NLTK punkt tokenizer downloaded successfully")

# Check for stopwords
try:
    find('corpora/stopwords')
    logger.info("NLTK stopwords found locally")
except LookupError:
    logger.info("NLTK stopwords not found locally, downloading...")
    download('stopwords', quiet=True)
    logger.info("NLTK stopwords downloaded successfully")


class SentimentAnalyzer:
    """
    Enhanced sentiment analyzer for stock reports.
    
    Version 1.0 - Cline implementation for Martin East - Implements sentiment analysis using VAD lexicon - Apr 13, 2025.
    """
    
    def __init__(self, lexicon_path=None, custom_stopwords=None):
        """
        Initialize the sentiment analyzer.
        
        Args:
            lexicon_path (str): Path to the NRC VAD lexicon file
            custom_stopwords (list): Additional stopwords to exclude
        """
        self.lexicon_path = lexicon_path or DEFAULT_LEXICON_PATH
        self.lexicon = self._load_lexicon()
        
        # Initialize stopwords
        self.stopwords = set(stopwords.words('english'))
        if custom_stopwords:
            self.stopwords.update(custom_stopwords)
        
        # Hedging words indicating uncertainty
        self.hedging_words = {
            'possibly', 'might', 'could', 'maybe', 'perhaps', 'seems', 
            'appears', 'likely', 'unlikely', 'probably', 'potentially',
            'supposedly', 'allegedly', 'reportedly', 'rumored', 'estimated',
            'approximately', 'around', 'about', 'roughly', 'generally',
            'somewhat', 'sometimes', 'occasionally', 'often', 'usually'
        }
        
        # Positive and negative financial terms
        self.financial_terms = {
            'positive': {
                'growth', 'profit', 'gain', 'increase', 'rise', 'up', 'bull', 
                'bullish', 'outperform', 'exceed', 'beat', 'strong', 'strength',
                'opportunity', 'potential', 'innovation', 'innovative', 'success',
                'successful', 'positive', 'improvement', 'improved', 'growing',
                'expansion', 'expanded', 'dividend', 'revenue', 'earnings'
            },
            'negative': {
                'loss', 'decline', 'decrease', 'fall', 'down', 'bear', 'bearish',
                'underperform', 'miss', 'weak', 'weakness', 'risk', 'risky',
                'threat', 'negative', 'downturn', 'downsizing', 'layoff', 'cut',
                'debt', 'liability', 'recession', 'inflation', 'volatility',
                'uncertainty', 'concern', 'warning', 'caution', 'struggle'
            }
        }
    
    def _load_lexicon(self):
        """
        Load the NRC VAD lexicon.
        
        Returns:
            pandas.DataFrame: Lexicon data
        """
        try:
            lexicon = pd.read_csv(
                self.lexicon_path, 
                sep='\t', 
                names=['Word', 'Valence', 'Arousal', 'Dominance']
            )
            # Set word as index for faster lookups
            lexicon.set_index('Word', inplace=True)
            logger.info(f"Loaded lexicon with {len(lexicon)} words")
            return lexicon
        except Exception as e:
            logger.error(f"Error loading lexicon: {e}")
            # Create an empty lexicon as fallback
            return pd.DataFrame(columns=['Valence', 'Arousal', 'Dominance'])
    
    def preprocess_text(self, text):
        """
        Preprocess text for sentiment analysis.
        
        Args:
            text (str): Input text
            
        Returns:
            list: List of preprocessed tokens
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and numbers
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords
        tokens = [token for token in tokens if token not in self.stopwords and len(token) > 1]
        
        return tokens
    
    def analyze_text(self, text):
        """
        Analyze text for sentiment.
        
        Args:
            text (str): Input text
            
        Returns:
            dict: Sentiment analysis results
        """
        tokens = self.preprocess_text(text)
        
        # Initialize counters
        valence_scores = []
        arousal_scores = []
        dominance_scores = []
        hedging_count = 0
        financial_pos_count = 0
        financial_neg_count = 0
        
        # Count words
        total_words = len(tokens)
        matched_words = 0
        
        # Analyze each token
        for token in tokens:
            # Check for hedging words
            if token in self.hedging_words:
                hedging_count += 1
            
            # Check for financial terms
            if token in self.financial_terms['positive']:
                financial_pos_count += 1
            elif token in self.financial_terms['negative']:
                financial_neg_count += 1
            
            # Look up in lexicon
            if token in self.lexicon.index:
                matched_words += 1
                valence = self.lexicon.loc[token]['Valence']
                arousal = self.lexicon.loc[token]['Arousal']
                dominance = self.lexicon.loc[token]['Dominance']
                
                valence_scores.append(valence)
                arousal_scores.append(arousal)
                dominance_scores.append(dominance)
        
        # Calculate averages
        avg_valence = np.mean(valence_scores) if valence_scores else 0.5
        avg_arousal = np.mean(arousal_scores) if arousal_scores else 0.5
        avg_dominance = np.mean(dominance_scores) if dominance_scores else 0.5
        
        # Calculate confidence (inverse of hedging ratio)
        confidence = 1 - (hedging_count / total_words) if total_words else 1
        
        # Calculate financial sentiment
        financial_ratio = (financial_pos_count - financial_neg_count) / total_words if total_words else 0
        
        # Calculate coverage (percentage of words found in lexicon)
        coverage = matched_words / total_words if total_words else 0
        
        return {
            'valence': avg_valence,
            'arousal': avg_arousal,
            'dominance': avg_dominance,
            'confidence': confidence,
            'financial_sentiment': financial_ratio,
            'coverage': coverage,
            'total_words': total_words,
            'matched_words': matched_words,
            'hedging_words': hedging_count,
            'financial_positive': financial_pos_count,
            'financial_negative': financial_neg_count
        }
    
    def analyze_sentences(self, text):
        """
        Analyze sentiment at the sentence level.
        
        Args:
            text (str): Input text
            
        Returns:
            list: List of sentence-level sentiment analyses
        """
        sentences = sent_tokenize(text)
        results = []
        
        for sentence in sentences:
            sentiment = self.analyze_text(sentence)
            results.append({
                'sentence': sentence,
                'sentiment': sentiment
            })
        
        return results
    
    def get_emotional_summary(self, analysis):
        """
        Generate an emotional summary based on sentiment analysis.
        
        Args:
            analysis (dict): Sentiment analysis results
            
        Returns:
            dict: Emotional summary
        """
        # Interpret valence
        if analysis['valence'] > 0.67:
            valence_label = "positive"
        elif analysis['valence'] < 0.33:
            valence_label = "negative"
        else:
            valence_label = "neutral"
        
        # Interpret arousal
        if analysis['arousal'] > 0.67:
            arousal_label = "excited"
        elif analysis['arousal'] < 0.33:
            arousal_label = "calm"
        else:
            arousal_label = "moderate"
        
        # Interpret dominance
        if analysis['dominance'] > 0.67:
            dominance_label = "dominant"
        elif analysis['dominance'] < 0.33:
            dominance_label = "submissive"
        else:
            dominance_label = "neutral"
        
        # Interpret confidence
        if analysis['confidence'] > 0.8:
            confidence_label = "very confident"
        elif analysis['confidence'] > 0.6:
            confidence_label = "confident"
        elif analysis['confidence'] > 0.4:
            confidence_label = "somewhat confident"
        else:
            confidence_label = "uncertain"
        
        # Interpret financial sentiment
        if analysis['financial_sentiment'] > 0.1:
            financial_label = "bullish"
        elif analysis['financial_sentiment'] < -0.1:
            financial_label = "bearish"
        else:
            financial_label = "neutral"
        
        return {
            'emotional_tone': f"{valence_label} and {arousal_label}",
            'power_dynamic': dominance_label,
            'certainty': confidence_label,
            'market_outlook': financial_label,
            'primary_emotion': self._get_primary_emotion(
                analysis['valence'], 
                analysis['arousal'], 
                analysis['dominance']
            )
        }
    
    def _get_primary_emotion(self, valence, arousal, dominance):
        """
        Map VAD values to a primary emotion.
        
        Args:
            valence (float): Valence score
            arousal (float): Arousal score
            dominance (float): Dominance score
            
        Returns:
            str: Primary emotion
        """
        # Simplified emotion mapping based on VAD space
        if valence > 0.67:
            if arousal > 0.67:
                if dominance > 0.67:
                    return "excited"
                else:
                    return "happy"
            else:
                if dominance > 0.67:
                    return "confident"
                else:
                    return "content"
        elif valence < 0.33:
            if arousal > 0.67:
                if dominance > 0.67:
                    return "angry"
                else:
                    return "fearful"
            else:
                if dominance > 0.67:
                    return "disappointed"
                else:
                    return "sad"
        else:
            if arousal > 0.67:
                return "alert"
            elif arousal < 0.33:
                return "calm"
            else:
                return "neutral"
    
    def get_key_emotional_terms(self, text, top_n=10):
        """
        Extract key emotional terms from the text.
        
        Args:
            text (str): Input text
            top_n (int): Number of top terms to return
            
        Returns:
            dict: Top emotional terms by category
        """
        tokens = self.preprocess_text(text)
        
        # Filter tokens that are in the lexicon
        emotional_terms = {}
        
        for token in tokens:
            if token in self.lexicon.index:
                emotional_terms[token] = {
                    'valence': self.lexicon.loc[token]['Valence'],
                    'arousal': self.lexicon.loc[token]['Arousal'],
                    'dominance': self.lexicon.loc[token]['Dominance'],
                }
        
        # Sort terms by each dimension
        valence_terms = sorted(
            emotional_terms.items(), 
            key=lambda x: x[1]['valence'], 
            reverse=True
        )
        
        arousal_terms = sorted(
            emotional_terms.items(), 
            key=lambda x: x[1]['arousal'], 
            reverse=True
        )
        
        dominance_terms = sorted(
            emotional_terms.items(), 
            key=lambda x: x[1]['dominance'], 
            reverse=True
        )
        
        # Get top terms
        top_valence_positive = [term[0] for term in valence_terms[:top_n]]
        top_valence_negative = [term[0] for term in valence_terms[-top_n:]]
        top_arousal = [term[0] for term in arousal_terms[:top_n]]
        top_dominance = [term[0] for term in dominance_terms[:top_n]]
        
        return {
            'positive_terms': top_valence_positive,
            'negative_terms': top_valence_negative,
            'high_arousal_terms': top_arousal,
            'high_dominance_terms': top_dominance
        }
    
    def get_one_word_summary(self, analysis):
        """
        Generate a one-word summary of the sentiment.
        
        Args:
            analysis (dict): Sentiment analysis results
            
        Returns:
            str: One-word summary
        """
        summary = self.get_emotional_summary(analysis)
        return summary['primary_emotion'].upper()

class StockReportAnalyzer:
    """
    Analyzer for stock reports.
    
    Version 1.0 - Cline implementation for Martin East - Analyzes stock reports for emotional content - Apr 13, 2025.
    """
    
    def __init__(self, sentiment_analyzer=None):
        """
        Initialize the stock report analyzer.
        
        Args:
            sentiment_analyzer (SentimentAnalyzer): Sentiment analyzer instance
        """
        self.sentiment_analyzer = sentiment_analyzer or SentimentAnalyzer()
    
    def analyze_report(self, report_path=None, report_text=None):
        """
        Analyze a stock report.
        
        Args:
            report_path (str): Path to the report file
            report_text (str): Report text (alternative to report_path)
            
        Returns:
            dict: Analysis results
        """
        # Get report text
        if report_text is None:
            if report_path is None:
                report_path = DEFAULT_REPORT_PATH
            
            try:
                with open(report_path, 'r') as f:
                    report_text = f.read()
                logger.info(f"Loaded report from {report_path}")
            except Exception as e:
                logger.error(f"Error loading report: {e}")
                return {
                    'error': f"Failed to load report: {str(e)}",
                    'success': False
                }
        
        # Analyze the full report
        overall_sentiment = self.sentiment_analyzer.analyze_text(report_text)
        
        # Analyze by sentence
        sentence_analysis = self.sentiment_analyzer.analyze_sentences(report_text)
        
        # Get emotional summary
        emotional_summary = self.sentiment_analyzer.get_emotional_summary(overall_sentiment)
        
        # Get key emotional terms
        key_terms = self.sentiment_analyzer.get_key_emotional_terms(report_text)
        
        # Get one-word summary
        one_word = self.sentiment_analyzer.get_one_word_summary(overall_sentiment)
        
        # Compile results
        results = {
            'overall_sentiment': overall_sentiment,
            'emotional_summary': emotional_summary,
            'key_terms': key_terms,
            'one_word_summary': one_word,
            'sentence_analysis': sentence_analysis,
            'success': True
        }
        
        return results
    
    def save_analysis(self, analysis, output_path=None):
        """
        Save analysis results to a file in the cache directory.
        
        Args:
            analysis (dict): Analysis results
            output_path (str, optional): Output file path. If None, uses default path in cache directory.
            
        Returns:
            bool: Success status
        """
        try:
            # Convert sentence analysis to a serializable format
            if 'sentence_analysis' in analysis:
                for item in analysis['sentence_analysis']:
                    item['sentence'] = str(item['sentence'])
            
            # Ensure cache directory exists
            cache_dir = Path("./cache")
            cache_dir.mkdir(exist_ok=True)
            
            # Use default path in cache directory if not specified
            if output_path is None:
                output_path = cache_dir / "sentiment_analysis.json"
            
            with open(output_path, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            logger.info(f"Analysis saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            return False
    
    def print_summary(self, analysis):
        """
        Print a summary of the analysis.
        
        Args:
            analysis (dict): Analysis results
        """
        if not analysis.get('success', False):
            print(f"Analysis failed: {analysis.get('error', 'Unknown error')}")
            return
        
        print("\n=== STOCK REPORT SENTIMENT ANALYSIS ===\n")
        
        # Print overall sentiment
        sentiment = analysis['overall_sentiment']
        print(f"VALENCE: {sentiment['valence']:.3f} (Negative to Positive)")
        print(f"AROUSAL: {sentiment['arousal']:.3f} (Calm to Excited)")
        print(f"DOMINANCE: {sentiment['dominance']:.3f} (Submissive to Dominant)")
        print(f"CONFIDENCE: {sentiment['confidence']:.3f} (Uncertain to Certain)")
        print(f"FINANCIAL SENTIMENT: {sentiment['financial_sentiment']:.3f} (Bearish to Bullish)")
        
        # Print emotional summary
        summary = analysis['emotional_summary']
        print(f"\nEMOTIONAL TONE: {summary['emotional_tone']}")
        print(f"POWER DYNAMIC: {summary['power_dynamic']}")
        print(f"CERTAINTY: {summary['certainty']}")
        print(f"MARKET OUTLOOK: {summary['market_outlook']}")
        print(f"PRIMARY EMOTION: {summary['primary_emotion']}")
        
        # Print one-word summary
        print(f"\nONE WORD SUMMARY: {analysis['one_word_summary']}")
        
        # Print key terms
        print("\nKEY EMOTIONAL TERMS:")
        print(f"  Positive: {', '.join(analysis['key_terms']['positive_terms'][:5])}")
        print(f"  Negative: {', '.join(analysis['key_terms']['negative_terms'][:5])}")
        print(f"  High Arousal: {', '.join(analysis['key_terms']['high_arousal_terms'][:5])}")
        print(f"  High Dominance: {', '.join(analysis['key_terms']['high_dominance_terms'][:5])}")
        
        print("\n=========================================\n")


def main():
    """
    Main function for testing the module.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze sentiment in stock reports')
    parser.add_argument('--report', type=str, default=DEFAULT_REPORT_PATH, 
                       help='Path to the stock report file')
    parser.add_argument('--lexicon', type=str, default=DEFAULT_LEXICON_PATH,
                       help='Path to the NRC VAD lexicon file')
    parser.add_argument('--output', type=str, default='./sentiment_analysis.json',
                       help='Output file for analysis results')
    args = parser.parse_args()
    
    try:
        # Create sentiment analyzer
        sentiment_analyzer = SentimentAnalyzer(lexicon_path=args.lexicon)
        
        # Create stock report analyzer
        report_analyzer = StockReportAnalyzer(sentiment_analyzer)
        
        # Analyze report
        analysis = report_analyzer.analyze_report(report_path=args.report)
        
        # Print summary
        report_analyzer.print_summary(analysis)
        
        # Save analysis
        if report_analyzer.save_analysis(analysis, args.output):
            print(f"Analysis saved to {args.output}")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        print(f"Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
