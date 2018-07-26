import platform


def windows_multiprocessing_with_django():
    """
    On windows multi-processing the default is to spawn a new process, in contrast to
    *nix fork().  This means that the new processes aren't being setup in the same
    manner, most notably django is not setup because the new process starts a new
    interpreter that only loads a minimal set of packages.  It enters execution in a
    different place.  Therefore, when using multi-processing ON WINDOWS this needs
    called BEFORE any imports to packages using django, including those deriving
    from django.
    """
    if platform.system() == 'Windows':
        import django
        from django.apps import apps
        if not apps.ready:
            django.setup()