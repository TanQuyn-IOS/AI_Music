from rest_framework.renderers import BaseRenderer


class AudioRenderer(BaseRenderer):
    media_type = 'audio/*'
    format = 'audio'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


class MidiRenderer(BaseRenderer):
    media_type = 'audio/midi'
    format = 'midi'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data
