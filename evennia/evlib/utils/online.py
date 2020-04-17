import evennia


def sessions():
    """
    Simple shortcut to retrieving all connected sessions.

    Returns:
        list
    """
    return evennia.SESSION_HANDLER.values()


def accounts():
    """
    Uses the current online sessions to derive a list of connected players.

    Returns:
        list
    """
    return sorted([acc for acc in evennia.SESSION_HANDLER.all_connected_accounts()], key=lambda acc: acc.key)


def puppets():
    """
    Uses the current online sessions to derive a list of connected characters.

    Returns:
        list
    """
    characters = {puppet for session in sessions() if (puppet := session.get_puppet())}
    return sorted(list(characters), key=lambda char: char.key)


def admin_chars():
    """
    Filters characters() by who counts as an admin!
    Also returns online accounts who are admin and have no characters logged in.

    :return: list
    """
    return set([char for char in puppets() if char.locks.check_lockstring(char, 'dummy:perm(Admin)')])


def admin_accounts():
    """
    Filters characters() by who counts as an admin!
    Also returns online accounts who are admin and have no characters logged in.

    :return: list
    """
    return set([acc for acc in accounts() if acc.locks.check_lockstring(acc, 'dummy:perm(Admin)')])
