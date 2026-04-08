try:
    from ._version import version as __version__
except ImportError:
    __version__ = 'unknown'


from napari_animation_timeline.animation_timeline import AnimationTimeline

__all__ = ('AnimationTimeline',)
