from flask import session, has_request_context

def get_current_user_id():
    if has_request_context():
        user_id = session.get("user_id")

        if not user_id:
            raise Exception("User belum login")

        return user_id

    return 1