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
    partner_zodiac_sign = SelectField(
        "Preferred Zodiac Sign",
        choices=[
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ],validators=[DataRequired()]
    )
    partner_min_age = IntegerField("Partner Min Age", validators=[DataRequired(), NumberRange(min=18, max=99)])
    partner_max_age = IntegerField("Partner Max Age", validators=[DataRequired(), NumberRange(min=18, max=99)])
    partner_min_height = IntegerField("Partner Min Height (cm)", validators=[DataRequired(), NumberRange(min=100, max=250)])
    partner_max_height = IntegerField("Partner Max Height (cm)", validators=[DataRequired(), NumberRange(min=100, max=250)])
    partner_min_weight = IntegerField("Partner Min Weight (kg)", validators=[DataRequired(), NumberRange(min=30, max=150)])
    partner_max_weight = IntegerField("Partner Max Weight (kg)", validators=[DataRequired(), NumberRange(min=30, max=150)])