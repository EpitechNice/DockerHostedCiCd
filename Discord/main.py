from discord import app_commands
from typing import Literal
import discord
import json
import sys
import os

SERVER_ID       = 1204010822502850580

PERSO_CAT_ID    = 1204031320452235314

WELCOME_CHAN_ID = 1204041986701664308
LOGS_CHAN_ID    = 1243492927544496240

MEMBER_ROLE_ID  = 1204053915658752081

BOT_ID          = 1204033816096673812

# 🔴・ Project Name
# 🔵・ Project Name

intents = discord.Intents.all()
client  = discord.Client(intents=intents)
tree    = app_commands.CommandTree(client)

# Globals
#   Guild
server          = None

#   Category
perso_chat_cat  = None

#   Channel
welcome         = None
logs            = None

#   Role
member_role     = None


personal_chans = {}
# {
#     user_id: chan_id
# }

projects_chans = {}
# {
#     category_id: {
#         "text_id": text_channel_id,
#         "voc_id": vocal_channel_id,
#         "project_over": True if project is over, False otherwise,
#         "collaborators" = [
#             user_id,
#             user_id,
#             ...
#         ]
#     }
# }

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_TOKEN  = os.getenv("GITHUB_TOKEN")

if DISCORD_TOKEN is None or GITHUB_TOKEN is None:
    print("DISCORD_TOKEN and GITHUB_TOKEN env variables must be set !!")
    sys.exit(1)

def save_infos(filename: str, data: dict):
    with open(filename, 'w+') as f:
        json.dump(data, f, indent=4)

def load_infos(filename: str) -> dict:
    with open(filename, 'r') as f:
        return json.load(f)

@tree.command(
    name="addproject",
    description="Add a project",
    guild=discord.Object(id=SERVER_ID)
)
async def add_project(interaction, name: str, description: str, language: Literal["C", "C++", "Python"]):
    await interaction.response.send_message("Hello!")

@client.event
async def on_ready():
    global server, perso_chat_cat, welcome, logs, member_role
    server          = client.get_guild(SERVER_ID)
    perso_chat_cat  = discord.Object(id=PERSO_CAT_ID)
    welcome         = client.get_channel(WELCOME_CHAN_ID)
    logs            = client.get_channel(LOGS_CHAN_ID)
    member_role     = server.get_role(MEMBER_ROLE_ID)

    if any(obj is None for obj in [server, perso_chat_cat, welcome, logs, member_role]):
        print("An error occured while creating global objects !")
        sys.exit(1)

    await tree.sync(guild=server)
    print("[+] Bot running")

@client.event
async def on_member_join(member: discord.Member):
    global personal_chans
    overrides = {
        server.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True)
    }
    await welcome.send(f"Say hello to {member.name} !")
    await member.add_roles(member_role)
    print(f"{member.name} joined the server")
    channel = await server.create_text_channel(f"🔵・chat-{member.global_name}", category=perso_chat_cat, overwrites=overrides)
    personal_chans[member.id] = channel.id
    save_infos("./personnals.json", personal_chans)

@client.event
async def on_member_remove(member: discord.Member):
    global personal_chans
    print(f"{member.name} left the server")
    try:
        await welcome.send(f"Goodbye {member.name}")
        channel = server.get_channel(personal_chans[member.id])
    except:
        print(f"Could not find {member.id} in {personal_chans}")
    else:
        await channel.delete()
        del personal_chans[member.id]
        save_infos("./personnals.json", personal_chans)

@client.event
async def on_message_edit(before: discord.message.Message, after: discord.message.Message):
    if (after.author.id == BOT_ID):
        return
    global logs
    if logs is None:
        logs = client.get_channel(LOGS_CHAN_ID)
    embed = discord.Embed(
        title     = "Message edited",
        timestamp = after.created_at,
        colour    = discord.Colour(0xEB6107)
    )
    embed.set_author(name=f'{before.author.name}', icon_url=before.author.avatar.url)
    embed.add_field(
        name   = "Before",
        value  = f"`{before.content}`",
        inline = False
    )
    embed.add_field(
        name   = "After",
        value  = f"`{after.content}`",
        inline = False
    )
    embed.add_field(
        name   = "Message",
        value  = f"[Go to the edited message]({after.jump_url})"
    )
    await logs.send(embed=embed)

@client.event
async def on_message_delete(message: discord.message.Message):
    if (message.author.id == BOT_ID):
        return
    global logs
    if logs is None:
        logs = client.get_channel(LOGS_CHAN_ID)
    embed = discord.Embed(
        title     = "Message deleted",
        colour    = discord.Colour(0xF10F00),
    )
    embed.set_author(name=f'{message.author.name}', icon_url=message.author.avatar.url)
    embed.add_field(
        name   = "Message",
        value  = f"`{message.content}`",
        inline = False
    )
    await logs.send(embed=embed)

if not os.path.isfile("./personnals.json"):
    save_infos("./personnals.json", personal_chans)

if not os.path.isfile("./projects.json"):
    save_infos("./projects.json", projects_chans)

personal_chans = load_infos("./personnals.json")
projects_chans = load_infos("./projects.json")

client.run(DISCORD_TOKEN)
