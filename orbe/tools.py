"""Compatibility imports for the original Orbe editor API."""
from .ui.editors import (
    section, slider, toggle_row, slider_row, dims_text, ToolWindow,
    CropView, CropWindow,
    AddBgWindow,
    Shape, draw_shape, AnnotateView, AnnotateWindow,
    RedactView, RedactWindow,
    EditWindow,
    MetadataWindow,
    CompressWindow,
    ResizeWindow,
    ProtectWindow,
)
from .ui.editors.background import PRESETS, SOLIDS
