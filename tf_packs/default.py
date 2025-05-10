from packs import *
import re
import random

def tics_simple_speech_repl(options : dict[float, str]) -> Callable[[str, float], str]:
    def tics(content : str, bias : float) -> str:
        content_words = re.findall(r"[\w'\"]+|[.,!?;:\- ]", content)
        new_content = ""
        for i in range(len(content_words)):
            if content_words[i] in ".,!?;: ":
                new_content += content_words[i]
            else:
                new_content += content_words[i] if random.random() > bias else random.choices(list(options.values()), options.keys())[0]
        return new_content
    return tics

forms.append(TFState("dog", "Dog", None, None, tics_simple_speech_repl({0.45: "bark", 0.35: "woof", 0.2: "arf"}), "__user__ transformed into a dog!"))
forms.append(TFState("cat", "Cat", None, None, tics_simple_speech_repl({0.6: "meow", 0.3: "mrow", 0.1: "mreow"}), "__user__ transformed into a cat!"))
forms.append(TFState("bird", "Bird", None, None, tics_simple_speech_repl({0.2: "chirp", 0.3: "scree", 0.1: "screech", 0.2: "scraw", 0.2: "rawk", 0.1: "craw"}), "__user__ transformed into a bird!"))