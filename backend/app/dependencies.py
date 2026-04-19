# This is the ONLY place models are loaded.
# They are loaded ONCE at application startup via the
# lifespan context manager in main.py.
# All routes receive them via FastAPI Depends().
# This avoids @lru_cache on mutable objects and prevents
# race conditions under concurrent requests.

import sys
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("reviewsense.dependencies")

# Module-level singletons — set during lifespan startup
_model = None
_vectorizer = None
_models_loaded = False


def add_src_to_path():
    """Add src/ to sys.path so all src imports work."""
    from app.config import get_settings
    settings = get_settings()
    src_path = str(settings.src_dir)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    # Also add project root for absolute imports
    root_path = str(settings.src_dir.parent)
    if root_path not in sys.path:
        sys.path.insert(0, root_path)
    logger.info(f"sys.path updated: src={src_path}")


def _patch_streamlit_cache():
    """
    Patch @st.cache_resource and @st.cache_data so that src/ modules
    that use Streamlit caching decorators work outside Streamlit.
    The patches turn the decorators into plain lru_cache / no-ops.
    """
    try:
        import streamlit as st
        # If streamlit is importable, check if we're running
        # inside a Streamlit app or standalone
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        ctx = get_script_run_ctx()
        if ctx is not None:
            # We're inside Streamlit — no patching needed
            return
    except Exception:
        pass

    # Either streamlit is not installed or we're outside Streamlit.
    # Provide stub decorators so @st.cache_resource / @st.cache_data
    # don't crash when src.models.sentiment etc. are imported.
    import types
    from functools import lru_cache

    st_module = types.ModuleType("streamlit")

    def _cache_resource(func=None, *, show_spinner=True, ttl=None, **kwargs):
        if func is None:
            return lambda f: lru_cache(maxsize=1)(f)
        return lru_cache(maxsize=1)(func)

    def _cache_data(func=None, *, show_spinner=True, ttl=None, **kwargs):
        if func is None:
            return lambda f: lru_cache(maxsize=128)(f)
        return lru_cache(maxsize=128)(func)

    st_module.cache_resource = _cache_resource
    st_module.cache_data = _cache_data

    # Add common streamlit attributes so other imports don't crash
    st_module.error = lambda *a, **kw: None
    st_module.warning = lambda *a, **kw: None
    st_module.info = lambda *a, **kw: None
    st_module.write = lambda *a, **kw: None
    st_module.spinner = lambda *a, **kw: __import__("contextlib").nullcontext()

    sys.modules["streamlit"] = st_module
    logger.info("Patched streamlit module for non-Streamlit environment")


def load_artifacts():
    """
    Load model and vectorizer from models/ directory.
    Called ONCE during application startup.
    Imports load_model from src — do not rewrite this logic.
    """
    global _model, _vectorizer, _models_loaded
    if _models_loaded:
        return

    add_src_to_path()
    _patch_streamlit_cache()

    try:
        from src.predict import load_model as src_load_model
        _model, _vectorizer = src_load_model()
        _models_loaded = True
        logger.info("✅ Models loaded successfully at startup")
    except ImportError as e:
        logger.error(f"Failed to import src.predict: {e}")
        logger.info("Attempting fallback joblib load...")
        _load_artifacts_fallback()
    except Exception as e:
        logger.error(f"Model loading failed: {e}")
        raise RuntimeError(
            f"Cannot start API — model loading failed: {e}"
        )


def _load_artifacts_fallback():
    """
    Fallback: load pkl files directly with joblib.
    Used if src.predict.load_model does not exist.
    """
    global _model, _vectorizer, _models_loaded
    import joblib
    from app.config import get_settings
    settings = get_settings()

    model_candidates = [
        "classical/best_model.pkl",
        "classical/linearsvc.pkl",
        "classical/sentiment_model.pkl",
        "sentiment_model.pkl",
        "best_model.pkl",
        "linearSVC.pkl",
    ]
    vectorizer_candidates = [
        "classical/tfidf_vectorizer.pkl",
        "vectorizer.pkl",
        "tfidf_vectorizer.pkl",
        "tfidfvectorizer.pkl",
    ]

    for name in model_candidates:
        path = settings.model_dir / name
        if path.exists():
            _model = joblib.load(path)
            logger.info(f"Loaded model from {path}")
            break

    for name in vectorizer_candidates:
        path = settings.model_dir / name
        if path.exists():
            _vectorizer = joblib.load(path)
            logger.info(f"Loaded vectorizer from {path}")
            break

    if _model is None or _vectorizer is None:
        # For transformer-based pipelines, model/vectorizer
        # may not be needed as pkl files — mark as loaded
        # since the transformer loads internally
        logger.warning(
            "Could not find classical model/vectorizer pkl files "
            f"in {settings.model_dir}. "
            "Transformer models will be loaded on first prediction."
        )
        _model = None
        _vectorizer = {"info": "Transformer mode — no classical vectorizer"}

    _models_loaded = True


def get_model() -> Any:
    """FastAPI dependency — returns loaded model."""
    if not _models_loaded:
        raise RuntimeError(
            "Models not loaded. "
            "Ensure load_artifacts() ran during startup."
        )
    return _model


def get_vectorizer() -> Any:
    """FastAPI dependency — returns loaded vectorizer."""
    if not _models_loaded:
        raise RuntimeError(
            "Models not loaded. "
            "Ensure load_artifacts() ran during startup."
        )
    return _vectorizer
