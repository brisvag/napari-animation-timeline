from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qt_animation_timeline import AnimationTimelineWidget

if TYPE_CHECKING:
    import napari

# centralized whitelisted set of track options.
# Each key: value pair is in the form:
#     TrackName: 'attribute_path_from_source_model
_VIEWER_TRACK_OPTIONS = {
    'ndisplay': 'dims.ndisplay',
    'dims slider': 'dims.point',
    'dims margins': 'dims.thickness',
    'dims ': 'dims.current_step',
    'view direction': 'camera.angles',
    'zoom': 'camera.zoom',
    'dims': 'dims',
    'camera': 'camera',
}

# {layer_name} will be replaced by the actual name
_LAYER_TRACK_OPTIONS = {
    '{layer_name} - visibility': 'visible',
    '{layer_name} - opacity': 'opacity',
    '{layer_name} - blending': 'blending',
    '{layer_name} - transform': '_transforms',
    '{layer_name} - clipping planes': 'experimental_clipping_planes',
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
        self.layer_track_options = {}
        self.custom_track_options = {}

        super().__init__(track_options=self.viewer_track_options)

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

        self._update_track_options()

    def _update_track_options(self):
        self.animation.track_options = (
            self.viewer_track_options
            | self.custom_track_options
            | {
                k: v
                for dct in self.layer_track_options.values()
                for k, v in dct.items()
            }
        )
        for track in list(self.animation.tracks):
            if track.name not in self.animation.track_options:
                self.animation.remove_track(track)

    def _update_layer_track_names(self, event):
        layer = event.source
        new_opts = {}
        for (old_name, old_val), name_template in zip(
            self.layer_track_options[layer].items(),
            _LAYER_TRACK_OPTIONS,
            strict=True,
        ):
            new_name = name_template.format(layer_name=layer.name)
            self.animation.rename_track(old_name, new_name)
            new_opts[new_name] = old_val

        self.layer_track_options[layer] = new_opts

    def add_custom_track(self, name: str, model: Any, attr: str):
        """Add a custom animation track to the timeline.

        A custom track can be added to control any model attribute.
        For example, to control `my_model.color.hue`, you may pass:
        `timeline.add_custom_track('MyModel hue', MyModel.color, 'hue')`
        """
        self.custom_track_options[name] = (model, attr)
        self._update_track_options()

    def remove_custom_track(self, name: str):
        """Remove a previously added custom track."""
        self.custom_track_options.pop(name)
        self._update_track_options()
