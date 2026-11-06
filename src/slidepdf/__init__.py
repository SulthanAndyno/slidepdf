"""SlidePDF Studio - Professional PPTX to PDF Converter.

A modern, multi-engine PowerPoint presentation to PDF conversion suite
featuring standalone desktop GUI, CLI, batch processing, PDF merging,
and cross-platform support.
"""

__version__ = "1.0.0"
__author__ = "SlidePDF Team"
__license__ = "MIT"

import logging
# Silence internal noisy pypdf stream warnings
logging.getLogger("pypdf").setLevel(logging.ERROR)
