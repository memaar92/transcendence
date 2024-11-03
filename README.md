# transcendence

This is an reimagination of the classic Pong game. It was developed as part of the curriculum at 42. The project serves as a playground to explore frontend and backend integration, database handling, authentication, and secure communication.

## Features
- Game Modes: Matchmaking system for online players, round-robin tournaments and local game support
- User Profiles: Customizable profile, including avatars, auto-generated displaynames and game history
- User Authentication: Secure sign-up and login, with support for two-factor authentication for enhanced security. 42 third-party-auth
- Chat Functionality: Real-time one-on-one chat with support for message history and notifications
- Friends System: Users can add friends, block users, send game invites, and view online statuses

## Tech Stack
- Frontend: Plain Javascript/HTML/CSS
- Backend: Django & Django REST framework for efficient API creation
- Database: PostgreSQL for structured and scalable data storage, Redis as in-memory database
- WebSocket: Real-time communication implemented using WebSocket to handle live chat and gameplay
- Authentication: JWT stored inside httpOnly cookies, 2FA via authenticator app, OTP for email verification, OAuth 2.0 for third-party auth
- Docker: Containerized development and deployment using Docker for consistency and scalability

## Preview


https://github.com/user-attachments/assets/09d4cc86-9cf6-4a56-9d8d-049152a285f1





## Running the app
Follow these instructions to get your copy of the project up and running on your local machine for development and testing purposes.

1. Clone the repo
```
git clone https://github.com/memaar92/transcendence.git
```

2. Create a "secrets" folder in the root directory. The following files need to be present in this folder
```
Admin panel access:
django_admin_email.txt
django_admin_password.txt
django_admin_user.txt

Database setup:
postgresql_database.txt
postgresql_password.txt
postgresql_su_password.txt
postgresql_user.txt

Provide cryptographic signing. Django will refuse to start if SECRET_KEY is not set. Generate it.
secret_key.txt

OTP email for email verification. To print the OTP in the console instead, uncomment "print("send email with otp", otp)" in backend/usermanagement/views.py (and comment out the line "send_otp_email(user_profile.email, otp)"
email_host.txt 
email_host_pw.txt

42 third-party login (requires the creation of an OAuth 2.0 application on the 42 Intra platform
oauth_client_id.txt
oauth_secret.txt
```

3. Start the application from the root directory. Make will run docker compose
```
cd transcendence
make
```

4. Visit the application
```
https://localhost
OR
https://<Your local IP address>
```



