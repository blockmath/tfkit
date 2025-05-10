import revolt
import asyncio
from typing import Callable
from packs import *
import time
import pickle
import atexit
import json

bot_token = "****************************************************************"
data = None
with open("config.json", "r") as cfg:
    data = json.load(cfg)
bot_token = data["token"]

import tf_packs.default
import tf_packs.pokemon

class UserState:
    id : str
    form : TFState
    bias : float
    lock : int # 0: Unlocked, 1: Locked until set time, 2: Locked indefinitely (only user can revert), 3: Locked 'permanently'
    lock_until : float
    def __init__(self, user_id : str) -> None:
        self.id = user_id
        self.form = default_tf_state
        self.bias = 0.0
        self.lock = 0
        self.lock_until = 0.0
    
    def __getstate__(self):
        self.form_id = self.form.name
        self.form = None
        return self.__dict__
    
    def __setstate__(self, d):
        self.__dict__ = d
        self.form = default_tf_state
        for form in forms:
            if form.name.lower() == self.form_id.lower():
                self.form = form
        self.form_id = None

    
    def is_form_locked(self, is_self_tf : bool) -> bool:
        if self.lock == 0:
            return False
        elif self.lock == 1:
            if time.time() >= self.lock_until:
                self.lock = 0
                return False
            else:
                return True
        elif self.lock == 2:
            return not is_self_tf
        elif self.lock == 3:
            return True
    
    def set_form(self, req : revolt.Message, who : str, form_name : str, bias : float | None) -> str:
        if form_name == "revert_force" and req.author.get_permissions().manage_nicknames:
            self.form = default_tf_state
            self.bias = 0
            self.lock = 0
            return self.form.get_tf_message(who)


        if self.is_form_locked(who == "You"):
            if self.lock == 1:
                return f"You can't change back until <t:{self.lock_until}>!"
            elif self.lock == 2:
                return f"You can't transform {who} because they've locked their form!"
            elif self.lock == 3:
                return f"You can't change back! The TF is permanent!"

        if form_name == "revert":
            self.form = default_tf_state
            self.bias = bias if bias is not None else self.bias
            return self.form.get_tf_message(who)
        for form in forms:
            if form.name.lower() == form_name.lower():
                self.form = form
                self.bias = bias if bias is not None else self.bias
                return self.form.get_tf_message(who)
        return f"Couldn't find what a/an '{form_name.capitalize()}' is."
    
    def get_name(self, default_name : str) -> str:
        if self.form.name_override is None:
            return default_name
        else:
            return self.form.name_override
    def get_avatar(self, default_avatar : str) -> str:
        if self.form.avatar is None:
            return default_avatar
        else:
            return self.form.avatar
    def get_colour(self, default_colour : str) -> str:
        if self.form.colour is None:
            return default_colour
        else:
            return self.form.colour
    def tics(self, content : str) -> str:
        if self.form.tics is None:
            return content
        else:
            return self.form.tics(content, self.bias)

class ServerState:
    id : str
    users : dict[str, UserState]
    def __init__(self, server_id : str) -> None:
        self.id = server_id
        self.users = {}
    
    def get_user(self, user_id : str) -> UserState:
        if user_id not in self.users.keys():
            self.users[user_id] = UserState(user_id)
        return self.users.get(user_id)


servers : dict[str, ServerState] = {}

def is_float(s : str) -> bool:
    try:
        f = float(s)
    except ValueError:
        return False
    return True

class Client(revolt.Client):
    async def on_message(self, message : revolt.Message):
        if message.server_id not in servers.keys():
            servers[message.server_id] = ServerState(message.server_id)

        if message.author.id == self.user.id:
            return

        server = servers.get(message.server_id)
        user = server.get_user(message.author.id)

        await message.delete()
        await message.channel.send(message.content if message.content[0] == "/" else user.tics(message.content), masquerade=revolt.Masquerade(user.get_name(message.author.display_name), user.get_avatar(message.author.avatar.url), user.get_colour(message.author.roles[0].colour)))

        if message.content.split(" ")[0] == "/tf":
            match message.content.split(" ")[1:]:
                case ["lock"]:
                    match user.lock:
                        case 0:
                            user.lock = 2
                            await message.channel.send(f"You locked your form!")
                        case 1:
                            await message.channel.send(f"Your form is already locked until <t:{user.lock_until}>!")
                        case 2:
                            await message.channel.send(f"Your form is already locked!")
                        case 3:
                            await message.channel.send(f"Your form is already permanently locked!")
                case ["set", ("perma" | "permanent")]:
                    match user.lock:
                        case 0|1|2:
                            user.lock = 3
                            await message.channel.send(f"You permanently locked your form!")
                        case 3:
                            await message.channel.send(f"Your form is already permanently locked!")
                case [who, "set", ("perma" | "permanent")]:
                    if not message.author.get_permissions().manage_nicknames:
                        await message.channel.send(f"You don't have permission to perform this action.")
                    else:
                        server.get_user(who[2:-1]).lock = 3
                        await message.channel.send(f"{who}'s form became permanently locked!")
                case ["lock", "until", selected_time]:
                    match user.lock:
                        case 0,2:
                            user.lock = 1
                            user.lock_until = time.strptime(selected_time).timestamp
                        case 1:
                            await message.channel.send(f"Your form is already locked until <t:{user.lock_until}>!")
                        case 3:
                            await message.channel.send(f"Your form is already permanently locked!")
                case ["lock", "for", time_amount, time_increment]:
                    ti : float = 1.0
                    match time_increment.lower():
                        case "s"|"sec"|"seconds":
                            ti = 1.0
                        case "m"|"min"|"minutes":
                            ti = 60.0
                        case "h"|"hr"|"hours":
                            ti = 3600.0
                    match user.lock:
                        case 0,2:
                            user.lock = 1
                            user.lock_until = time.time() + (float(time_amount) * ti)
                        case 1:
                            await message.channel.send(f"Your form is already locked until <t:{user.lock_until}>!")
                        case 3:
                            await message.channel.send(f"Your form is already permanently locked!")
                case ["unlock"]:
                    match user.lock:
                        case 0,2:
                            user.lock = 0
                            await message.channel.send(f"You unlocked your form!")
                        case 1:
                            await message.channel.send(f"Your form is locked until <t:{user.lock_until}>!")
                        case 3:
                            await message.channel.send(f"Your form is permanently locked!")
                case [what]:
                    await message.channel.send(user.set_form(message, "You", what, None))
                case [what, bias] if is_float(bias):
                    await message.channel.send(user.set_form(message, "You", what, float(bias)))
                case [who, what] if who[0] == "<" and who[1] == "@" and who[-1] == ">":
                    target_user = server.get_user(who[2:-1])
                    await message.channel.send(target_user.set_form(message, who, what, None))
                case [who, what, bias] if who[0] == "<" and who[1] == "@" and who[-1] == ">" and is_float(bias):
                    target_user = server.get_user(who[2:-1])
                    await message.channel.send(target_user.set_form(message, who, what, float(bias)))
                case _:
                    await message.channel.send(f"Unknown command from {message.author.nickname}: {message.content}")


async def main():
    async with revolt.utils.client_session() as session:
        client = Client(session, bot_token)
        await client.start()

def save_server_data() -> None:
    with open("server_data.dat", "wb") as file:
        pickle.dump(servers, file)


with open("server_data.dat", "rb") as file:
    servers = pickle.load(file)

atexit.register(save_server_data)
asyncio.run(main())