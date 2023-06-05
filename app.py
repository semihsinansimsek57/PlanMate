import os
from os import listdir

import pdfkit as pdfkit
from flask import Flask, flash, redirect, render_template, request, session, jsonify, send_from_directory, url_for, \
    abort
from werkzeug.debug import console

from flask_session import Session
from models import User, Event, db_session, GuestList, Guest
from tempfile import mkdtemp
import bcrypt
from helpers import login_required, send_email, is_logged_in, generate_event_invitation, send_invitations_func
import re
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from flask_wtf.csrf import CSRFProtect, generate_csrf, CSRFError
import secrets
import logging
import openai
from forms import EventForm
import json

logging.basicConfig(level=logging.DEBUG)


def shutdown_session(exception=None):
    db_session.remove()


app = Flask(__name__)

app.config['SECRET_KEY'] = secrets.token_urlsafe(16)
openai.api_key = "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"

csrf = CSRFProtect(app)

app.debug = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        print("Current user_id in session:", session.get('user_id'))  # Add this line
        logged_in = is_logged_in()
        if session.get('user_id') is None:
            return render_template('landingpage.html', logged_in=logged_in)
        else:
            # Get the email verification status of the user from the database
            user = db_session.query(User).filter_by(user_id=session['user_id']).first()

            if user is None:
                return render_template('landingpage.html', logged_in=logged_in)

            email_verified = user.verified

            # If email is verified, show home page
            if email_verified:
                # Get the events of the user from the database
                events = db_session.query(Event).filter_by(event_creator_id=session['user_id']).all()
                return render_template('home.html', events=events, logged_in=logged_in)
            # If email is not verified, redirect to email verification page
            else:
                return redirect('/verify_email')


@app.route('/login', methods=['GET', 'POST'])
def login():
    logged_in = is_logged_in()
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']

        # Validate form data
        if not username or not password:
            error = 'Please fill in all the fields'
            return render_template('login.html', error=error, logged_in=logged_in)

        # Check if user exists in database.db, users table, use the SQLAlchemy
        user = db_session.query(User).filter_by(username=username).first()

        # If user does not exist, show error message
        if not user:
            error = 'Username does not exist'
            return render_template('login.html', error=error, logged_in=logged_in)

        # If user exists, check if password is correct
        if bcrypt.checkpw(password.encode('utf-8'), user.password):
            # If password is correct, set session variable and redirect to home page
            session['user_id'] = user.user_id
            print(session['user_id'])
            return redirect('/')
        else:
            error = 'Incorrect password'
            return render_template('login.html', error=error, logged_in=logged_in)
    else:
        return render_template('login.html', logged_in=logged_in)


@app.route('/register', methods=['GET', 'POST'])
def register():
    logged_in = is_logged_in()
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']

        # Validate form data
        if not username or not password or not confirm_password or not email:
            error = 'Please fill in all the fields'
            return render_template('register.html', error=error, logged_in=logged_in)
        elif password != confirm_password:
            error = 'Passwords do not match'
            return render_template('register.html', error=error, logged_in=logged_in)
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            error = 'Invalid email address'
            return render_template('register.html', error=error, logged_in=logged_in)
        elif not re.match(r"^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[a-zA-Z]).{8,}$", password):
            error = 'Password must be at least 8 characters long and contain at least one uppercase letter, ' \
                    'one lowercase letter, and one number'
            return render_template('register.html', error=error, logged_in=logged_in)

        # Check if user already exists in database.db, users table, use the SQLAlchemy
        user = db_session.query(User).filter_by(username=username).first()

        # If user already exists, show error message
        if user:
            error = 'Username already exists'
            return render_template('register.html', error=error, logged_in=logged_in)

        # Check if email already exists in database.db, users table, use the SQLAlchemy
        user = db_session.query(User).filter_by(email=email).first()
        # If email already exists, show error message
        if user:
            error = 'Email already exists'
            return render_template('register.html', error=error, logged_in=logged_in)

        # Hash password using bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        # Generate a random string for the email verification token
        email_verification_token = str(uuid.uuid4())
        # Insert user into database
        user = User(username=username, password=password_hash, email=email, verification_code=email_verification_token)
        db_session.add(user)
        db_session.commit()

        # Prompt a message to the console for debugging purposes
        print('User registered')

        # Automatically log in the user
        user_id = db_session.query(User).filter_by(username=username).first()
        session['user_id'] = user_id.user_id

        print('User registered')

        # Redirect to email verification page
        return redirect('/verify_email')

    # If request is GET, show registration form
    return render_template('register.html', logged_in=logged_in)


# Email verification page
@app.route('/verify_email', methods=['GET', 'POST'])
@login_required
def verify_email():
    # Get the email verification status of the user from the database
    user = db_session.query(User).filter_by(user_id=session['user_id']).first()
    email_verified = user.verified
    logged_in = is_logged_in()

    if request.method == 'GET':
        # If email is verified, redirect to home page
        if email_verified:
            return redirect('/')
        # If email is not verified, send email verification email then show email verification page
        else:
            # Get the email address and username of the user from the database
            user = db_session.query(User).filter_by(user_id=session['user_id']).first()
            email = user.email
            username = user.username

            # Get the email verification token of the user from the database
            user = db_session.query(User).filter_by(user_id=session['user_id']).first()
            email_verification_token = user.verification_code

            # Send email verification email
            send_email(email, email_verification_token, username)

            # Show email verification page
            return render_template('verify_email.html', logged_in=logged_in)

    # If request is POST, verify email
    else:
        # Get form data
        email_verification_token = request.form['verification_token']
        # Get the email verification token of the user from the database
        user = db_session.query(User).filter_by(user_id=session['user_id']).first()
        email_verification_token_db = user.verification_code

        # If the email verification token entered by the user matches the email verification token in the database,
        # verify the email
        if email_verification_token == email_verification_token_db:
            # Update the email verification status in the database
            user = db_session.query(User).filter_by(user_id=session['user_id']).first()
            user.verified = True
            db_session.commit()
            # Show home page
            return redirect('/')

        # If the email verification token entered by the user does not match the email verification token in the
        # database, show error message
        else:
            error = 'Invalid email verification token'
            return render_template('verify_email.html', error=error, email_verified=email_verified, logged_in=logged_in)


# Logout route
@app.route('/logout')
@login_required
def logout():
    # Remove user from session
    session.pop('user_id')
    # Return a message to the console for debugging purposes
    print('User logged out')
    return redirect('/')


# Create event route
@app.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    is_modal = request.args.get('is_modal', 'false') == 'true'  # Capture the is_modal query parameter
    hide_navbar = request.args.get('hide_navbar', default=False, type=bool)  # Capture the hide_navbar query parameter
    logged_in = is_logged_in()

    static_img_path = "static/icons/premade_event_images/staticimg"
    animated_img_path = "static/icons/premade_event_images/animatedimg"

    static_images = [f for f in os.listdir(static_img_path) if os.path.isfile(os.path.join(static_img_path, f))]
    animated_images = [f for f in os.listdir(animated_img_path) if os.path.isfile(os.path.join(animated_img_path, f))]

    if request.method == 'POST':
        event_name = request.form['event_name']
        event_description = request.form['event_description']
        event_date = request.form['event_date']
        event_time = request.form['event_time']
        event_location = request.form['event_location']
        event_organizer = request.form['event_organizer']
        event_organizer_email = request.form['event_organizer_email']
        event_organizer_phone = request.form['event_organizer_phone']
        event_organizer_website = request.form['event_organizer_website']
        selected_image_path = request.form['selected_image_path']

        if not event_name or not event_description or not event_date or not event_time or not event_location or not event_organizer or not event_organizer_email or not event_organizer_phone or not event_organizer_website or not selected_image_path:
            error = 'Please fill in all the fields'
            return render_template('create_event.html', error=error, logged_in=logged_in, is_modal=is_modal,
                                   hide_navbar=hide_navbar, static_images=static_images,
                                   animated_images=animated_images)

        event_date = datetime.strptime(event_date, '%Y-%m-%d')
        event_time = datetime.strptime(event_time, '%H:%M').time()

        user_id = session['user_id']

        event = Event(event_name=event_name, event_description=event_description, event_date=event_date,
                      event_time=event_time, event_location=event_location, event_organizer=event_organizer,
                      event_organizer_email=event_organizer_email, event_organizer_phone=event_organizer_phone,
                      event_organizer_website=event_organizer_website, event_image=selected_image_path,
                      event_creator_id=user_id)

        try:
            db_session.add(event)
            db_session.commit()
        except SQLAlchemyError as e:
            db_session.rollback()
            print("Error: " + str(e))

        print('Event created')

        return redirect('/')

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if is_ajax:
        return render_template('create_event_form.html', is_modal=is_modal, hide_navbar=hide_navbar,
                               static_images=static_images, animated_images=animated_images)

    return render_template('create_event.html', is_modal=is_modal, hide_navbar=hide_navbar, logged_in=logged_in,
                           static_images=static_images, animated_images=animated_images)


@app.route('/events_list')
@login_required
def events_list():
    events = Event.query.filter_by(event_creator_id=session['user_id']).all()
    return render_template('events_list.html', events=events)


@app.route('/<path:filename>')
@login_required
def serve_image(filename):
    return send_from_directory(os.path.join('.'), filename)


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return str(e), 400


@app.route('/guests_manage', methods=['GET', 'POST'])
@login_required
@csrf.exempt  # We will handle CSRF tokens in AJAX requests manually
def guests_manage():
    user_id = session['user_id']
    guest_lists = db_session.query(GuestList).filter_by(guest_list_creator_id=user_id).all()
    guests_data = db_session.query(Guest).join(GuestList).filter(GuestList.guest_list_creator_id == user_id).all()
    logged_in = is_logged_in()

    if request.method == 'POST':
        logging.debug(f"Received POST request: {request.form}")
        operation = request.form['operation']
        logging.debug(f"Operation: {operation}")

        if operation == 'get_data':
            guest_lists_data = [{'id': guest_list.guest_list_id, 'name': guest_list.guest_list_name,
                                 'description': guest_list.guest_list_description} for guest_list in guest_lists]
            guests_data = [
                {'id': guest.guest_id, 'name': guest.guest_name, 'email': guest.guest_email, 'phone': guest.guest_phone,
                 'guest_list_id': guest.guest_list_id} for guest in guests_data]
            return jsonify({'guest_lists': guest_lists_data, 'guests': guests_data})

        elif operation == 'create_guest_list':
            name = request.form['name']
            description = request.form['description']
            guest_list = GuestList(guest_list_name=name, guest_list_description=description,
                                   guest_list_creator_id=user_id)
            db_session.add(guest_list)
            db_session.commit()
            return '', 204
        elif operation == 'create_guest':
            guest_list_id = request.form['guest_list_id']
            guest_name = request.form['name']
            guest_email = request.form['email']
            guest_phone = request.form['phone']
            guest = Guest(guest_name=guest_name, guest_email=guest_email, guest_phone=guest_phone,
                          guest_list_id=guest_list_id)
            db_session.add(guest)
            db_session.commit()
            return '', 204
        elif operation == 'update_guest_list':
            guest_list_id = request.form['guest_list_id']
            new_name = request.form['new_name']
            new_description = request.form['new_description']
            guest_list = db_session.query(GuestList).get(guest_list_id)
            if guest_list and guest_list.guest_list_creator_id == user_id:
                guest_list.guest_list_name = new_name
                guest_list.guest_list_description = new_description
                db_session.commit()
                return '', 204
            else:
                abort(403)
        elif operation == 'delete_guest_list':
            guest_list_id = request.form['guest_list_id']
            guest_list = db_session.query(GuestList).get(guest_list_id)
            if guest_list and guest_list.guest_list_creator_id == user_id:
                db_session.delete(guest_list)
                db_session.commit()
                return '', 204
            else:
                abort(403)
        elif operation == 'delete_guest':
            guest_id = request.form['guest_id']
            guest = db_session.query(Guest).get(guest_id)
            guest_list = db_session.query(GuestList).get(guest.guest_list_id)
            if guest and guest_list.guest_list_creator_id == user_id:
                db_session.delete(guest)
                db_session.commit()
                return '', 204
            else:
                abort(403)
        else:
            logging.debug("Invalid operation, returning 400 Bad Request")
            return '', 400  # Return a bad request status if the request doesn't match any operation

    return render_template('guests.html', guest_lists=guest_lists, guests=guests_data, logged_in=logged_in)


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    user_id = session['user_id']
    user = db_session.query(User).get(user_id)
    logged_in = is_logged_in()

    if request.method == 'POST':
        operation = request.form.get('operation')

        if operation == 'update_username':
            new_username = request.form.get('new_username')
            # Perform any necessary validation on the new username

            if new_username == user.username:
                flash('Username is the same as the current one.', 'warning')
                return redirect(url_for('account'))

            if db_session.query(User).filter_by(username=new_username).first():
                flash('Username already exists.', 'danger')
                return redirect(url_for('account'))

            if not new_username:
                flash('Username cannot be empty.', 'danger')
                return redirect(url_for('account'))

            user.username = new_username
            db_session.commit()
            flash('Username updated successfully.', 'success')
            return redirect('/')

        elif operation == 'update_email':
            new_email = request.form.get('new_email')
            # Perform any necessary validation on the new email
            # Send a verification email

            if new_email == user.email:
                flash('Email is the same as the current one.', 'warning')
                return redirect(url_for('account'))

            if db_session.query(User).filter_by(email=new_email).first():
                flash('Email already exists.', 'danger')
                return redirect(url_for('account'))

            if not new_email:
                flash('Email cannot be empty.', 'danger')
                return redirect(url_for('account'))

            user.email = new_email
            user.email_verified = False
            db_session.commit()
            flash('Email updated successfully. Please verify your new email address.', 'success')
            return redirect('/verify_email')

        elif operation == 'delete_account':
            # Delete the user's account and all associated data from all tables
            guest_lists = db_session.query(GuestList).filter_by(guest_list_creator_id=user_id).all()
            for guest_list in guest_lists:
                db_session.query(Guest).filter_by(guest_list_id=guest_list.guest_list_id).delete()
                db_session.delete(guest_list)
            db_session.query(Event).filter_by(event_creator_id=user_id).delete()
            db_session.delete(user)
            db_session.commit()
            flash('Account deleted successfully.', 'success')

            # Redirect the user to the home or login page after account deletion
            return redirect('/')

        else:
            # Return an error if the operation is not recognized
            flash('Invalid operation.', 'danger')

    return render_template('account.html', logged_in=logged_in)


@app.route('/create_invitation', methods=['POST', 'GET'])
@login_required
def create_invitation():
    logged_in = is_logged_in()

    if request.method == 'POST':
        event_id = request.form['event_id']
        event = db_session.query(Event).get(event_id)
        event_creator_id = session['user_id']
        event_creator = db_session.query(User).get(event_creator_id)

        event_template = generate_event_invitation(event.event_name, event.event_date, event.event_time, event.event_location, event_creator.username)

        # id the user has not their own subdirectory in the "invitations" folder, create one
        if not os.path.exists(os.path.join('invitations', str(event_creator_id))):
            os.makedirs(os.path.join('invitations', str(event_creator_id)))

        # create the invitation file
        with open(os.path.join('invitations', str(event_creator_id), event.event_name + '.html'), 'w') as invitation_file:
            invitation_file.write(event_template)

    events = db_session.query(Event).filter_by(event_creator_id=session['user_id']).all()
    # Find the invitations that have been created for the user's events
    invitations = []
    for event in events:
        if os.path.exists(os.path.join('invitations', str(event.event_creator_id), event.event_name + '.html')):
            invitations.append(event)
    return render_template('create_invitation.html', logged_in=logged_in, events=events, invitations=invitations)


@app.route('/serve_invitation/<user_id>/<event_name>', methods=['GET'])
@login_required
def serve_invitation(user_id, event_name):
    print(f"User ID: {user_id}, Event Name: {event_name}")
    if int(user_id) != session['user_id']:
        print("Unauthorized access")
        return "Unauthorized", 403

    if not os.path.exists(os.path.join('invitations', str(user_id), event_name + '.html')):
        print("File not found")
        return "File not found", 404

    with open(os.path.join('invitations', str(user_id), event_name + '.html'), 'r') as invitation_file:
        invitation = invitation_file.read()
        return invitation


@app.route('/send_invitations', methods=['GET', 'POST'])
@login_required
def send_invitations():
    if request.method == 'GET':
        # If the user has not created any invitations yet, redirect them to the create invitation page
        if not os.path.exists(os.path.join('invitations', str(session['user_id']))):
            flash('You have not created any invitations yet.', 'warning')
            return redirect(url_for('create_invitation'))

        # Get the user's list of invitations from the "invitations" folder
        invitations = []
        for invitation in os.listdir(os.path.join('invitations', str(session['user_id']))):
            invitations.append(invitation[:-5])

        # If the user has no invitations, redirect them to the create invitation page
        if not invitations:
            flash('You have not created any invitations yet.', 'warning')
            return redirect(url_for('create_invitation'))

        # Get the user's guest lists
        guest_lists = db_session.query(GuestList).filter_by(guest_list_creator_id=session['user_id']).all()

        return render_template('send_invitations.html', logged_in=is_logged_in(), invitations=invitations, guest_lists=guest_lists)

    elif request.method == 'POST':
        event_name = request.form['invitation_id']
        guest_list_id = request.form['guest_list_id']

        # Get the user's guest list
        guest_list = db_session.query(GuestList).filter_by(guest_list_creator_id=session['user_id'], guest_list_id=guest_list_id).first()
        if not guest_list:
            flash('Guest list not found.', 'danger')
            return redirect(url_for('send_invitations'))

        # Get the guests using the guest list
        guests = db_session.query(Guest).filter_by(guest_list_id=guest_list.guest_list_id).all()
        if not guests:
            flash('Guest list is empty.', 'danger')
            return redirect(url_for('send_invitations'))

        # Get the invitation file using the event name
        if not os.path.exists(os.path.join('invitations', str(session['user_id']), event_name + '.html')):
            flash('Invitation not found.', 'danger')
            return redirect(url_for('send_invitations'))

        with open(os.path.join('invitations', str(session['user_id']), event_name + '.html'), 'r') as invitation_file:
            invitation = invitation_file.read()

        # Send the invitation to each guest
        send_invitations_func(guests, invitation)

        flash('Invitations sent successfully.', 'success')
        return redirect(url_for('send_invitations'))


@app.context_processor
def context_processor():
    return dict(csrf_token=generate_csrf())


if __name__ == '__main__':
    app.run(debug=True)
