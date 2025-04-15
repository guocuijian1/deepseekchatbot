import uuid

from chat_service import ChatUtil


def set_session_id_to_cookie(request, response):
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
    else:
        session_id = cookie.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            response.set_cookie(
                'session_id',
                session_id,
                max_age=3600,
                path='/',
                secure=False,
                httponly=False
            )
    return session_id


def get_session_id_from_cookie(request):
    cookie = request.cookies
    if cookie and 'session_id' in cookie:
        return cookie['session_id']
    return None


def get_or_set_instance(session_id, instance_store, stream_enabled):
    if session_id not in instance_store:
        instance = ChatUtil.get_instance(stream_enabled=stream_enabled)
        instance_store[session_id] = instance
    else:
        instance = instance_store[session_id]
    return instance


__all__ = ['set_session_id_to_cookie', 'get_or_set_instance']
