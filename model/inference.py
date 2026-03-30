import logging
from typing import Optional

from transformers import pipeline

from config import MODEL_NAME

logger = logging.getLogger(__name__)

# Singleton emotion classification pipeline — loaded once at module level
_classifier = None


def _get_classifier():
    """Lazy-load and return the emotion classifier singleton"""
    global _classifier
    if _classifier is None:
        logger.info(f"Loading emotion classification model: {MODEL_NAME}")
        _classifier = pipeline(
            "text-classification",
            model=MODEL_NAME,
            return_all_scores=True,
            device=-1,  # CPU only (-1 for CPU, 0+ for GPU)
        )
        logger.info("Model loaded successfully")
    return _classifier


def _get_neutral_fallback() -> dict:
    """Return neutral emotion fallback when inference fails or input is empty"""
    return {
        "emotion_label": "neutral",
        "confidence": 1.0,
        "joy": 0.0,
        "anger": 0.0,
        "fear": 0.0,
        "disgust": 0.0,
        "sadness": 0.0,
        "surprise": 0.0,
        "neutral": 1.0,
    }


def _normalize_emotion_scores(scores: list[dict]) -> dict:
    """
    Normalize raw model output to emotion dict.
    
    Model returns list of {label, score} dicts.
    We aggregate them and find the max confidence label.
    """
    emotions = {
        "joy": 0.0,
        "anger": 0.0,
        "fear": 0.0,
        "disgust": 0.0,
        "sadness": 0.0,
        "surprise": 0.0,
        "neutral": 0.0,
    }
    
    # Populate from model scores
    for item in scores:
        label = item["label"].lower()
        score = round(item["score"], 4)
        if label in emotions:
            emotions[label] = score
    
    # Find emotion with highest confidence
    emotion_label = max(emotions, key=emotions.get)
    confidence = round(emotions[emotion_label], 4)
    
    return {
        "emotion_label": emotion_label,
        "confidence": confidence,
        **emotions,
    }


def run_inference(texts: list[str], batch_size: int = 32) -> list[dict]:
    """
    Run batched emotion inference on a list of texts.
    
    Args:
        texts: List of text strings to analyze
        batch_size: Number of texts to process per batch (default: 32)
        
    Returns:
        List of dicts with emotion analysis, one per input text:
        {
            "emotion_label": str,      # Label with highest score
            "confidence": float,        # Rounded to 4 decimal places
            "joy": float,
            "anger": float,
            "fear": float,
            "disgust": float,
            "sadness": float,
            "surprise": float,
            "neutral": float,
        }
    """
    classifier = _get_classifier()
    results = []
    
    # Process in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        
        for text in batch:
            # Handle empty or whitespace-only input
            if not text or not text.strip():
                logger.debug("Skipping empty/whitespace-only text")
                results.append(_get_neutral_fallback())
                continue
            
            try:
                # Run inference on single text
                scores = classifier(text)
                
                # Normalize and aggregate scores
                normalized = _normalize_emotion_scores(scores)
                results.append(normalized)
                
            except Exception as e:
                logger.error(f"Inference error for text: {text[:50]}... | Error: {e}")
                results.append(_get_neutral_fallback())
    
    return results
