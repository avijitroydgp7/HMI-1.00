import logging
import os

def setup_logging():
    """Configure logging to suppress Qt warnings and debug messages."""
    # Suppress Qt warnings
    logging.getLogger("PyQt6").setLevel(logging.ERROR)
    logging.getLogger("qtawesome").setLevel(logging.ERROR)
    
    # Configure our application logging
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    # Set specific loggers to DEBUG for development if needed
    if os.environ.get('DEBUG', '').lower() in ('true', '1', 'yes'):
        logging.getLogger('utils').setLevel(logging.DEBUG)
        logging.getLogger('services').setLevel(logging.DEBUG)
