from discord_webhook import DiscordWebhook, DiscordEmbed

def send_discord_signal(webhook_url, signal, image_path):
    webhook = DiscordWebhook(url=webhook_url)
    with open(image_path, "rb") as f:
        webhook.add_file(file=f.read(), filename="chart.png")
    embed = DiscordEmbed(title="New Trading Signal", description=str(signal), color=242424)
    webhook.add_embed(embed)
    webhook.execute() 