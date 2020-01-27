# lunchroulette

A slack bot to group random people together to grab lunch.

This was inspired by a random lunch grouping that I've seen people do manually. It turns out well, but it would be nice if this could be automated in some fashion!

# Usage

# Setup
This is a Slack App configured to run on Heroku currently.

# Heroku Setup
- Create a new Heroku app
- Set the SLACK_BOT_SCOPE Heroku config var as "bot,commands,reactions:read,chat:write:bot"
- Attach a Heroku Postgres instance (free tier works)
- Generate database credentials (these will be used for migrations)


# Slack App Setup
- Create a new app at https://api.slack.com/apps
- Add Slash commands to route to your heroku app's domain
- Configure Oath redirect url
- Configure The app scopes
- Use the Slack Client ID as the SLACK_CLIENT_ID Heroku config var
- Use the Slack Client Secret as the SLACK_CLIENT_SECRET Heroku config var
