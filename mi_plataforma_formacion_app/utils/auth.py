"""Small auth utilities for marking public routes."""
def public_route(view):
    """Mark a view as public so a global before_request can bypass login.

    Usage:
        @bp.route('/foo')
        @public_route
        def foo():
            ...
    """
    try:
        setattr(view, "_is_public_route", True)
    except Exception:
        # best-effort: if view is a functools.partial or wrapped object,
        # try to set attribute on the underlying function if available.
        try:
            if hasattr(view, '__wrapped__'):
                setattr(view.__wrapped__, "_is_public_route", True)
        except Exception:
            pass
    return view
