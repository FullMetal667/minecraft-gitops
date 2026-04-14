import discord
from discord.ext import commands

TOKEN = "YOUR_TOKEN"

bot = commands.Bot(command_prefix="!")

@bot.command()
async def atm10(ctx):
    await ctx.send(
        "Neue Version 6.6 erkannt. Möchtest du vorbereiten?",
        view=ConfirmView()
    )

class ConfirmView(discord.ui.View):
    @discord.ui.button(label="Ja", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button):
        await interaction.response.send_message("Update wird vorbereitet...")
        # Hier triggerst du dein Script

    @discord.ui.button(label="Nein", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button):
        await interaction.response.send_message("Abgebrochen.")

bot.run(TOKEN)
