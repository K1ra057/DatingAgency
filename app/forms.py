from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, TextAreaField, DateField
from wtforms.validators import DataRequired, Length, NumberRange

class ClientForm(FlaskForm):
    gender = SelectField("Gender", choices=[("male", "Male"), ("female", "Female")], validators=[DataRequired()])
    registration_date = DateField("Registration Date", validators=[DataRequired()])
    age = IntegerField("Age", validators=[DataRequired(), NumberRange(min=18, max=100)])
    height = IntegerField("Height (cm)", validators=[DataRequired(), NumberRange(min=50, max=250)])
    weight = IntegerField("Weight (kg)", validators=[DataRequired(), NumberRange(min=30, max=200)])
    zodiac_sign = StringField("Zodiac Sign", validators=[DataRequired(), Length(max=20)])
    self_description = TextAreaField("Self Description", validators=[Length(max=500)])
