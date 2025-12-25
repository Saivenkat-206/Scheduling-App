from enum import Enum

class Action(str, Enum):
    VIEW = "view"
    ADD = "add"
    EDIT = "edit"
    DELETE = "delete"
    IMPORT = "import"
    EXPORT = "export"


def is_allowed(user, action: Action, table_name: str) -> bool:
    """
    user: None for now
    """
    # 🚧 no auth yet — allow everything
    return True
