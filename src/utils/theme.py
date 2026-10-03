"""Theme preference persistence and stylesheet color adaptation."""


class ThemePreference:
    SETTINGS_KEY = "dark_mode"

    def __init__(self, settings):
        self.settings = settings
        self.enabled = self._to_bool(settings.value(self.SETTINGS_KEY, False))

    @staticmethod
    def _to_bool(value):
        if isinstance(value, str):
            return value.strip().casefold() in {"1", "true", "yes", "on"}
        return bool(value)

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        self.settings.setValue(self.SETTINGS_KEY, self.enabled)
        self.settings.sync()
        return self.enabled


def stylesheet_for_mode(light_stylesheet, dark_mode):
    """Return the supplied light stylesheet with a dark palette when enabled."""
    if not dark_mode:
        return light_stylesheet

    replacements = {
        "#d4d0c8": "#202124",
        "#000000": "#e8eaed",
        "#7f9db9": "#5f6368",
        "#316ac5": "#3c6eaf",
        "#e1e1e1": "#3c4043",
        "#7f7f7f": "#5f6368",
        "#eeeeee": "#4a4d50",
        "#c8c8c8": "#303134",
        "#777777": "#9aa0a6",
        "#e8e8e8": "#35363a",
        "#d6d6d6": "#3c4043",
        "#a0a0a0": "#5f6368",
        "#808080": "#5f6368",
        "#666666": "#9aa0a6",
    }
    for light, dark in replacements.items():
        light_stylesheet = light_stylesheet.replace(light, dark)

    return (
        light_stylesheet
        .replace("background-color: #ffffff;", "background-color: #292a2d;")
        .replace("border-top-color: #ffffff;", "border-top-color: #70757a;")
        .replace("border-left-color: #ffffff;", "border-left-color: #70757a;")
        .replace("border-bottom-color: #ffffff;", "border-bottom-color: #70757a;")
        .replace("border-right-color: #ffffff;", "border-right-color: #70757a;")
    )
