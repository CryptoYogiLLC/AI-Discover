"""
Celery tasks for AI-Discover
"""

from app.core.celery import celery_app

# Import all task modules here
# from .discovery import *
# from .sync import *


# Example task
@celery_app.task
def test_task(x: int, y: int) -> int:
    """Simple test task that adds two numbers"""
    return x + y
