# PlanMate
#### Video Demo:  <https://youtu.be/R5Y5q7ptdZ8>
#### Description: PlanMate is a web application that designed to help out event organizers. It allows users to create events, invite friends, and keep track of who is coming. It also allows users to create events, guest lists, guesses, automated invitations, and sending the invitations with just one click.

## Usage

After running the application, you can open it in a web browser at `http://localhost:5000`.

## Security

This application uses encrypted configuration files to securely store sensitive information like email credentials. I strongly advise against storing sensitive information in plain text or environment variables.

## Contribution

Contributions are welcome! Please read the [CONTRIBUTING](./CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## Acknowledgements

- CS50 for their helpful courses and tutorials.
- And of course, all the contributors who spend their time improving this project.

## app.py

This file contains the main implementation of the Planmate application. It is responsible for handling the Flask routes and managing the backend functionality.

### Dependencies

- `os`: Provides functions for interacting with the operating system.
- `pdfkit`: A Python library for converting HTML to PDF.
- `flask`: A micro web framework for building web applications.
- `flask_session`: Extension for managing user sessions in Flask.
- `bcrypt`: A password hashing library.
- `tempfile`: Provides functions for working with temporary files and directories.
- `werkzeug`: A WSGI utility library for handling HTTP requests and responses.
- `datetime`: Provides classes for manipulating dates and times.
- `sqlalchemy`: SQL toolkit and Object-Relational Mapping (ORM) library for Python.
- `flask_wtf`: Integration of Flask and WTForms, a flexible forms validation and rendering library.
- `secrets`: Generates secure random numbers for managing secrets.
- `logging`: Provides logging capabilities for debugging and error handling.
- `openai`: OpenAI Python library for accessing the OpenAI API.
- `forms`: Custom forms for user input validation.

### Functionality

The `app.py` file includes the following main functionalities:

- User authentication (login, registration, logout)
- Email verification
- Event creation, listing, and management
- Guest list creation, listing, and management
- Invitation creation and sending

### How to Run

To run the Planmate application locally, follow these steps:

1. Install the required dependencies by running the following command:
   ```bash
   pip install -r requirements.txt
   
    ```
2. Set the required environment variables. For example, you can create a .env file and add the following variables:
   ```
   SECRET_KEY=your_secret_key
   DATABASE_URL=your_database_url
   ```
3. Start the application by running the following command:
   ```bash
   flask run
   ```
   
4. Open the application in a web browser at `http://localhost:5000`.

5. Enjoy!

Note: Open your web browser and navigate to http://localhost:5000 to access the application.

### Routes

- `/`: The landing page that displays a login form if the user is not logged in, or the home page if the user is logged in.
- `/login`: The login page that displays a login form.
- `/register`: The registration page that displays a registration form.
- `/logout`: The logout route that logs the user out and redirects to the landing page.
- `/verify/<token>`: The email verification route that verifies the user's email address.
- `/home`: The home page that displays the user's events.
- `/create_event`: The event creation page that displays an event creation form.
- `/events_list`: The route for listing all events created by the user.
- `/guests_manage`: The route for managing guest lists and guests.
- `/account`: The user account settings page.
- `/create_invitation`: The route for creating event invitations.
- `/serve_invitation/<user_id>/<event_name>`: The route for serving event invitations.
- `/send_invitations`: The route for sending event invitations.

This is a brief overview of the app.py file in the Planmate project. Refer to the source code for detailed implementation and functionality.

Feel free to modify the above section to fit your project's specific details.


## SQLAlchemy Models

This repository contains the SQLAlchemy models for a database schema. The models are defined in the `models.py` file. Let's go through each model and its attributes.

### User

- Table Name: `users`
- Attributes:
  - `user_id`: Integer, Primary Key, Autoincrement
  - `username`: String(50), Not Null, Unique
  - `password`: String(50), Not Null
  - `email`: String(50), Not Null, Unique
  - `verified`: Boolean, Not Null, Default: False
  - `verification_code`: CHAR(36), Not Null
  - `created_at`: DateTime, Not Null, Default: Current datetime
  - `updated_at`: DateTime, Not Null, Default: Current datetime (on update)

### Event

- Table Name: `events`
- Attributes:
  - `event_id`: Integer, Primary Key, Autoincrement
  - `event_name`: String(50), Not Null
  - `event_description`: String(100), Not Null
  - `event_date`: DateTime, Not Null
  - `event_time`: Time, Not Null
  - `event_location`: String(50), Not Null
  - `event_organizer`: String(50), Not Null
  - `event_organizer_email`: String(50), Not Null
  - `event_organizer_phone`: String(50), Not Null
  - `event_organizer_website`: String(50), Not Null
  - `event_image`: String(255), Not Null
  - `created_at`: DateTime, Not Null, Default: Current datetime
  - `updated_at`: DateTime, Not Null, Default: Current datetime (on update)
  - `event_creator_id`: Integer, Foreign Key to `users.user_id`

### GuestList

- Table Name: `guest_lists`
- Attributes:
  - `guest_list_id`: Integer, Primary Key, Autoincrement
  - `guest_list_name`: String(50), Not Null
  - `guest_list_description`: String(100), Not Null
  - `created_at`: DateTime, Not Null, Default: Current datetime
  - `updated_at`: DateTime, Not Null, Default: Current datetime (on update)
  - `guest_list_creator_id`: Integer, Foreign Key to `users.user_id`

### Guest

- Table Name: `guests`
- Attributes:
  - `guest_id`: Integer, Primary Key, Autoincrement
  - `guest_name`: String(50), Not Null
  - `guest_email`: String(50), Not Null
  - `guest_phone`: String(50), Not Null
  - `created_at`: DateTime, Not Null, Default: Current datetime
  - `updated_at`: DateTime, Not Null, Default: Current datetime (on update)
  - `guest_list_id`: Integer, Foreign Key to `guest_lists.guest_list_id`

### Database Connection and Session

The database connection is established using SQLAlchemy and SQLite. The engine is created with the `create_engine` function, connecting to the `database.db` file.

```python
engine = create_engine('sqlite:///database.db', echo=True)
```

The tables are created in the database by calling the create_all() method on the Base.metadata object, passing the engine as the bind.
    
```python
Base.metadata.create_all(bind=engine)
```

Finally, a session is created using the sessionmaker object, binding it to the `engine


## Flask Forms

This repository also includes Flask forms for handling event data. The forms are defined in the `forms.py` file. Let's go through the form and its fields.

### EventForm

The `EventForm` is a FlaskForm used for capturing event details.

#### Fields:

- `event_name`: StringField, Title of the event, with a length validator (minimum: 2, maximum: 140 characters).
- `event_description`: TextAreaField, Description of the event, with a length validator (minimum: 2, maximum: 500 characters).
- `event_date`: DateField, Date of the event, with a validator for ensuring data is required.
- `event_time`: TimeField, Time of the event, with a validator for ensuring data is required.
- `event_location`: StringField, Location of the event, with a validator for ensuring data is required.
- `event_organizer`: StringField, Name of the event organizer, with a validator for ensuring data is required.
- `event_organizer_email`: StringField, Email of the event organizer, with validators for ensuring data is required and that the input follows the email format.
- `event_organizer_phone`: StringField, Phone number of the event organizer, with a validator for ensuring data is required.
- `event_organizer_website`: StringField, Website of the event organizer, with a validator for ensuring data is required.
- `event_image`: FileField, Image for the event, with a validator for ensuring data is required.

#### Meta:

The `Meta` class within the `EventForm` is used for configuring form-related settings.

- `csrf`: False, Disables Cross-Site Request Forgery (CSRF) protection for this form.

These forms can be used in Flask routes to validate and process user input for creating or updating events.


## Helper Functions

This repository includes several helper functions for common tasks. These functions are defined in the `helpers.py` file. Let's go through each function and its purpose.

### login_required

The `login_required` decorator function is used to decorate routes that require user authentication. It checks if a user is logged in by checking if the `user_id` is present in the session. If the user is not logged in, it redirects them to the login page.

### send_email

The `send_email` function is used to send verification emails to users. It takes the user's email, verification code, and username as parameters. The function loads the email configuration from encrypted files (`key.key` and `config.enc`), constructs the email message with the verification code, and sends it using the SMTP server.

### is_logged_in

The `is_logged_in` function checks if a user is currently logged in. It checks if the `user_id` is present in the session and verifies the user's existence in the database.

### generate_event_invitation

The `generate_event_invitation` function generates an HTML invitation for an event. It takes the event name, date, time, location, and organizer as parameters and creates an HTML template with placeholders. The placeholders are replaced with the event details, and the resulting HTML is returned.

### send_invitations_func

The `send_invitations_func` function sends event invitations to a list of guests. It takes the list of guests and the invitation HTML as parameters. The function loads the email configuration, creates the email message with the HTML content, and sends it to each guest's email address using the SMTP server.

These helper functions can be used in your Flask routes to perform common tasks such as user authentication, email sending, and event invitation generation.


## Templates

This repository includes several HTML templates for rendering the web pages. These templates are defined in the `templates` folder. Let's go through each template and its purpose.

- `index.html`: The base template that all other templates extend. It includes the navigation bar and footer.
- `login.html`: The login page template. It includes a form for logging in.
- `register.html`: The registration page template. It includes a form for registering a new user.
- `verify_email.html`: The verification page template. It includes a form for verifying a user's email address.
- `account.html`: The account page template. It includes a form for updating a user's account details.
- `create_event.html`: The create event page template. It includes a form for creating a new event.

And many more...


## Requirements

This repository uses Python 3.9.6 and the following packages:

- aiohttp==3.8.4
- aiosignal==1.3.1
- async-timeout==4.0.2
- attrs==22.2.0
- bcrypt==4.0.1
- cachelib==0.10.2
- certifi==2022.12.7
- cffi==1.15.1
- charset-normalizer==3.0.1
- click==8.1.3
- colorama==0.4.6
- cryptography==40.0.2
- decorator==5.1.1
- dnspython==2.3.0
- email-validator==1.3.1
- Flask==2.2.3
- Flask-Login==0.6.2
- Flask-Session==0.4.0
- Flask-SQLAlchemy==3.0.3
- Flask-WTF==1.1.1
- frozenlist==1.3.3
- greenlet==2.0.2
- idna==3.4
- itsdangerous==2.1.2
- Jinja2==3.1.2
- MarkupSafe==2.1.2
- multidict==6.0.4
- openai==0.27.4
- pdfkit==1.0.0
- pycparser==2.21
- requests==2.28.2
- self==2020.12.3
- SQLAlchemy==2.0.5.post1
- tqdm==4.65.0
- typing_extensions==4.5.0
- urllib3==1.26.14
- Werkzeug==2.2.3
- WTForms==3.0.1
- yarl==1.8.2




