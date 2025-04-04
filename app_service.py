import uuid
from datetime import datetime,timedelta


def set_or_check_session_id(request, response):
    cookie = request.cookies

    if not cookie:
        session_id = str(uuid.uuid4())
        response.set_cookie(
            'session_id',
            session_id,
            max_age=3600,
            path='/',
            secure=False,
            httponly=False
        )
        response.set_cookie(
            'last_modified_at',
            datetime.utcnow().isoformat(),
            max_age=30,
            path='/',
            secure=False,
            httponly=False
        )
        return session_id
    else:
        return cookie['session_id']


__all__ = ['set_or_check_session_id']
