from __future__ import annotations

from typing import TYPE_CHECKING

from qt_animation_editor import AnimationTimelineWidget
from qtpy.QtWidgets import QHBoxLayout, QWidget

if TYPE_CHECKING:
    import napari


class AnimationTimeline(QWidget):
    def __init__(self, viewer: napari.viewer.ViewerModel, **kwargs):
        super().__init__(**kwargs)
        track_options = {'Camera Angles': (viewer.camera, 'angles')}
        self.setLayout(QHBoxLayout())
        self.timeline = AnimationTimelineWidget(
            track_options=track_options, parent=self
        )
        self.layout().addWidget(self.timeline)
