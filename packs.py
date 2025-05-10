from typing import Callable
import re

class TFState:
    name : str
    name_override : str | None
    avatar : str | None
    colour : str | None
    tics : Callable[[str, float], str] | None
    tf_message : str
    def __init__(self, name : str, name_override : str | None, avatar : str | None, colour : str | None, tics : Callable[[str, float], str] | None, tf_message : str) -> None:
        self.name = name
        self.name_override = name_override
        self.avatar = avatar
        self.colour = colour
        self.tics = tics
        self.tf_message = tf_message
    def get_tf_message(self, who : str) -> str:
        message = self.tf_message
        message = re.sub("__user__", who, message)
        message = re.sub("__pronoun__", "your" if who == "You" else "their", message)
        return message


default_tf_state = TFState("", None, None, None, None, "__user__ transformed back into __pronoun__ normal form!")

forms : list[TFState] = []