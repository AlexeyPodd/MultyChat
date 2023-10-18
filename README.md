# MultyChat Application

## About application
MultyChat is a site for communication in chats. The idea is similar to a streamer services - each user can open a chat
and communicate with their audience in it. Private correspondence is also available in any chat.

### Roles and privileges of users
The chat owner can ban users and appoint moderators to help him. Administrators, appointed by the superuser, can ban
chat owners, prohibiting them from opening the chat, as well as ban users in all chats on the site,
possibly for an indefinite period. Each user can add any other user to his black list, and see his messages no more.

### Managing bans
Chat owner or appointed moderator can ban users right in chat. They can unban a banned user on the banana management
page.

Only the owner of the chat or the site administrator can ban indefinitely or unban a user who has been banned 
indefinitely.

The site administrator has access to the entire history of bans (except for canceled ones), and he can also see every
ban of any user and cancel (delete) it.

## Technical description
This application was created using Django framework, Django Channels for using WebSockets Protocol for chat messaging
and system commands between client and server. This system commands are used for adding users to black list, 
banning users, opening/closing chat, etc. right in chat page, using context menu in chat area. 
Ajax is used for managing bans, demoting moderators and excluding users from black list on corresponding pages.

## Launching of the project

##### Before launching project you would need to set .env file with environ variables in application root directory:
Django variables: SECRET_KEY, DEBUG, ALLOWED_HOSTS, DATABASE_HOST, REDIS_HOST

And Postgres variables: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB

Application is dockerized, so you can use docker-compose.yml file.
It uses runserver command, gunicorn & nginx not included.

For launching also needed standard manipulations - such as providing migrations, collecting static,
creating superuser, etc.