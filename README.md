# EOS Dapp Resource Monitoring and Alert (Telegram Bot)
With this repository, you can create a telegram bot and monitor you resources of your smart contract. Get autmatic notifications on a channel you set up via the bot if resources run low.

![Screenshot](https://github.com/oboluscrypto/eos-dapp-resource-alert/raw/master/monitoring.png "Telegram bot sends a warning")

## Requirements
Python 3.6+

pip install -r requirements.txt

## Set up telegram
### Create the bot
This is super easy, talk to the botfather bot and let him create a bot for you. Be sure to note the token it gives you. [More info](https://core.telegram.org/bots#creating-a-new-bot).
The token looks like `123456789:ZIUHDFIUHAIUFuqushfuia4UA1`.

### Add bot to channel and get channel id
Make a group for your alerts. Add the bot via its name. Then you can find the chat id by running:
https://api.telegram.org/bot123456789:ZIUHDFIUHAIUFuqushfuia4UA1/getUpdates (replace the token).

Check for the channel it was just added to and you'll see the id, something like `-11321241`.

## Setup this app
In `./configs` folder, cp the sample file to `eos-monitor.json`. Fill the three required files with token, chat id, and EOS account name to monitor. If the contract is on mainnet, make you pick up a node that is connected to mainnet.

## Limits
In the config file there are limits set. A warning will appear if you used resources in per cent (%) go above that limit.

Another message will appear in the chat if the resources drop below. Feel free to adjust the python code as necessary to your needs.


