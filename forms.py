from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField, BooleanField, DateField, SelectField, IntegerField, FloatField, SubmitField,TextAreaField
from wtforms.validators import InputRequired, Email, Length, DataRequired
from wtforms.fields.html5 import TelField, EmailField


class UserRegistrationForm(FlaskForm):
    FullName = StringField("",validators = [InputRequired(), Length(min=4, max=30)], render_kw={"placeholder": "Full Name"})
    EmailAddress = EmailField("",validators =[InputRequired(), Email()], render_kw={"placeholder": "Email Address"})
    UserType = SelectField("", validators=[InputRequired()], choices=[('student','Student'),('teacher','Teacher')])
    Username = StringField("",validators = [InputRequired(), Length(min=4, max=30)], render_kw={"placeholder": "@Username"})
    Password = PasswordField("", validators=[InputRequired(), Length(min=8,max=50)], render_kw={"placeholder": "Password"})
    Submit = SubmitField("Register")


class LoginForm(FlaskForm):
    Username = StringField("Username",validators = [InputRequired(), Length(min=4, max=30)], render_kw={"placeholder": "@Username"})
    Password = PasswordField("Password", validators=[InputRequired(), Length(min=8,max=50)], render_kw={"placeholder": "Password"})
    Remember = BooleanField('Remember me')
    Submit = SubmitField("Login")


class ClassroomForm(FlaskForm):
    ClassName = StringField("Class Name",validators = [InputRequired(), Length(min=2, max=100)], render_kw={"placeholder": "Class Name"})
    ClassDescription = TextAreaField("Class Description",validators = [InputRequired(), Length(min=20, max=200)], render_kw={"placeholder": "Class Description"})
    Submit = SubmitField("Create")


class ProblemForm(FlaskForm):
    ClassroomID = SelectField('Classroom', choices=[])
    ProblemDescription = TextAreaField("",validators = [InputRequired(), Length(min=2, max=500)], render_kw={"placeholder": "Problem description here"})
    FunctionName = StringField("",validators = [InputRequired(), Length(min=2, max=30)], render_kw={"placeholder": "Name of the function to evaluate"})
    SampleInput = StringField("",validators = [InputRequired(), Length(min=2, max=50)], render_kw={"placeholder": "Input data to check"})
    InputDataType = SelectField("", validators=[InputRequired()], choices=[('int','int'),('float','float'),('string','string')])
    ExpectedOutput = StringField("",validators = [InputRequired(), Length(min=2, max=200)], render_kw={"placeholder": "Expected output"})
    OutputDataType = SelectField("", validators=[InputRequired()], choices=[('int','int'),('float','float'),('string','string')])
    Submit = SubmitField("Create")


