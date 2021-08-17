def _jupyter_nbextension_paths():
    return [
        {
            "section": "notebook",
            "src": "static",
            "dest": "common_utils",
            "require": "common_utils/extension",
        }
    ]