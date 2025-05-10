# Using this bot

Follow the steps for setting up a Revolt bot. Put the bot token in `config.json` under `"token"`. Run `tfk.py`.

# Adding new species

Species are organized into packs (within `tf_packs`) for compartmentalization. For example, all Pokémon species are listed in `pokemon.py`.
If your species should be part of an existing pack, add it to that pack using the `forms.append()` statement.
If your species should be part of a new pack, create a new file in `tf_packs` called `<name_of_your_pack>.py`. This file should begin with `from packs import *`, followed by tic imports and definitions, followed by `forms.append()` statements. Add `import tf_packs.<name_of_your_pack>` near the top of `tfk.py`.
