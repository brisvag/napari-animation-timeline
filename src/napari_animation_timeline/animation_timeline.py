from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qt_animation_timeline import AnimationTimelineWidget

if TYPE_CHECKING:
    import napari

# centralized whitelisted set of track options.
# Each key: value pair is in the form:
#     TrackName: 'attribute_path_from_source_model
_VIEWER_TRACK_OPTIONS = {
    'Dims': 'dims',
    'Dims slider': 'dims.current_step',
    'Camera': 'camera',
    'Scale Bar': 'scale_bar',
}

# {layer_name} will be replaced by the actual name
_LAYER_TRACK_OPTIONS = {
    '{layer_name} - Visibility': 'visible',
    '{layer_name} - Opacity': 'opacity',
}


def _resolve_attr_path(source: Any, path: str) -> tuple[Any, str]:
    while True:
        attr, _, path = path.partition('.')
        if not path:
            return source, attr
        source = getattr(source, attr)


class AnimationTimeline(AnimationTimelineWidget):
    def __init__(self, viewer: napari.viewer.ViewerModel):
        self.viewer = viewer

        self.viewer_track_options = {
            name: _resolve_attr_path(viewer, attr_path)
            for (name, attr_path) in _VIEWER_TRACK_OPTIONS.items()
        }

        super().__init__(track_options=self.viewer_track_options)

        self.layer_track_options = {}
        self.viewer.layers.events.inserted.connect(self._update_layer_options)
        self.viewer.layers.events.removed.connect(self._update_layer_options)

    def _update_layer_options(self):
        for layer in self.viewer.layers:
            if layer in self.layer_track_options:
                continue
            self.layer_track_options[layer] = {
                name.format(layer_name=layer.name): _resolve_attr_path(
                    layer, attr_path
                )
                for (name, attr_path) in _LAYER_TRACK_OPTIONS.items()
            }
            layer.events.name.connect(self._update_layer_track_names)

        for layer in list(self.layer_track_options):
            if layer not in self.viewer.layers:
                self.layer_track_options.pop(layer)
                layer.events.name.disconnect(self._update_layer_track_names)

        track_options = dict(self.viewer_track_options)
        for l_opts in self.layer_track_options.values():
            track_options.update(l_opts)

        self.track_options = track_options

    def _update_layer_track_names(self, event):
        layer = event.source
        for track, name in zip(
            self.layer_track_options[layer],
            _LAYER_TRACK_OPTIONS.keys(),
            strict=True,
        ):
            new_name = name.format(layer_name=layer.name)
            self.rename_track(track, new_name)
            # print(track, new_name)
