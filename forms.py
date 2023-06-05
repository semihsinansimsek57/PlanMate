from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, TimeField, FileField, validators
from wtforms.validators import DataRequired, Length


class EventForm(FlaskForm):
    event_name = StringField("Title", validators=[Length(min=2, max=140)])
    event_description = TextAreaField("Description", validators=[Length(min=2, max=500)])
    event_date = DateField("Date", validators=[DataRequired()])
    event_time = TimeField("Time", validators=[DataRequired()])
    event_location = StringField("Location", validators=[DataRequired()])
    event_organizer = StringField("Organizer", validators=[DataRequired()])
    event_organizer_email = StringField("Organizer Email", validators=[DataRequired(), validators.Email()])
    event_organizer_phone = StringField("Organizer Phone", validators=[DataRequired()])
    event_organizer_website = StringField("Organizer Website", validators=[DataRequired()])
    event_image = FileField("Event Image", validators=[DataRequired()])

    class Meta:
        csrf = False
