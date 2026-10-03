from src.utils.theme import ThemePreference, stylesheet_for_mode


class MemorySettings:
    def __init__(self):
        self.values = {}
        self.sync_count = 0

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value

    def sync(self):
        self.sync_count += 1


def test_dark_mode_preference_persists_across_instances():
    settings = MemorySettings()

    first = ThemePreference(settings)
    assert first.enabled is False
    assert first.set_enabled(True) is True

    restarted = ThemePreference(settings)

    assert restarted.enabled is True
    assert settings.sync_count == 1


def test_dark_mode_preference_parses_qsettings_string_values():
    settings = MemorySettings()
    settings.values[ThemePreference.SETTINGS_KEY] = "true"

    assert ThemePreference(settings).enabled is True

    settings.values[ThemePreference.SETTINGS_KEY] = "false"
    assert ThemePreference(settings).enabled is False


def test_light_stylesheet_is_returned_unchanged():
    stylesheet = "QWidget { background-color: #d4d0c8; color: #000000; }"

    assert stylesheet_for_mode(stylesheet, False) == stylesheet


def test_dark_stylesheet_replaces_surface_and_text_colors():
    stylesheet = (
        "QWidget { background-color: #d4d0c8; color: #000000; }"
        "QLineEdit { background-color: #ffffff; selection-color: #ffffff; }"
    )

    dark_stylesheet = stylesheet_for_mode(stylesheet, True)

    assert "background-color: #202124" in dark_stylesheet
    assert "color: #e8eaed" in dark_stylesheet
    assert "background-color: #292a2d" in dark_stylesheet
    assert "selection-color: #ffffff" in dark_stylesheet
