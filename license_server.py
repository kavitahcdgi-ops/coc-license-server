#!/usr/bin/env python3
"""
License Server Application

A server for managing and serving licenses for the Code of Conduct project.
"""

import logging
from datetime import datetime


def main():
    """Main entry point for the license server."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("License Server started at %s", datetime.now().isoformat())


if __name__ == "__main__":
    main()
