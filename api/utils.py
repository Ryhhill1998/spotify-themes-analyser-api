from fastapi import Response


def set_response_cookie(response: Response, key: str, value: str):
    # must rememeber to set secure=True before production
    response.set_cookie(key=key, value=value, httponly=True, secure=False, samesite="lax")
