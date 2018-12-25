from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file
from wtforms.validators import InputRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user,current_user
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from wtforms.validators import InputRequired, Email, Length
from forms import *
from io import BytesIO
import os


import PyPDF2

from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = set(['txt','pdf'])


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'

##################################
# Connecting to the database and ORM as known sqlalchemy
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, scoped_session
from database_setup import *

engine = create_engine('sqlite:///classroom.db')
Base.metadata.bind = engine

# Creates the session
session = scoped_session(sessionmaker(bind=engine))


@app.teardown_request
def remove_session(ex=None):
    session.remove()


###############################

bootstrap = Bootstrap(app)

# Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
######################################


@login_manager.user_loader
def load_user(user_id):
    userId = session.query(Users).filter_by(UserIDNumber = int(user_id)).first()
    return userId


# Log out
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


# Password Reset
@app.route('/reset_password')
def reset_password():
    return 'password reset page'


# Registration System
@app.route('/register',  methods=['GET', 'POST'])
def register():

    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    RegForm = UserRegistrationForm()
    if RegForm.validate_on_submit():
        hashed_password = generate_password_hash(RegForm.Password.data, method='sha256')
        newUser = Users(FullName=RegForm.FullName.data, Username=RegForm.Username.data, UserType = RegForm.UserType.data, EmailAddress=RegForm.EmailAddress.data, Password=hashed_password)
        session.add(newUser)
        session.commit()

        return redirect(url_for('login'))
    return render_template('register.html', RegForm=RegForm)


# Login System
@app.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    loginForm = LoginForm()

    if loginForm.validate_on_submit():
        tempUser = loginForm.Username.data
        user = session.query(Users).filter_by(Username=tempUser).first()
        if user:
            if check_password_hash(user.Password, loginForm.Password.data):
                login_user(user, remember=loginForm.Remember.data)
                return redirect(url_for('dashboard'))
            else:
                flash("Password not correct")
                return redirect(url_for('login'))

    return render_template('login.html', LoginForm = loginForm)


# User type identifier
# Checks if the current user is Teacher or Not
def is_teacher(current_user):
    if current_user.UserType == 'teacher':
        return True
    else:
        return False


@app.route('/grades')
@login_required
def grades():
    grades = session.query(Grade).all()

    return render_template('grades.html', grades=grades)

# User Dashboard
# Uses the is_teacher() function to identify the user type
# and redirect to the target dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.UserType == 'student':
        enrollments = session.query(Classroom).join(Enrollment).filter(Classroom.ClassroomID == Enrollment.ClassroomID, Enrollment.UserIDNumber == current_user.UserIDNumber)
        return render_template('student_dashboard.html',enrollments=enrollments)
    elif current_user.UserType == 'teacher':
        return render_template('teacher_dashboard.html')
    else:
        return redirect(url_for('home'))


# Classrooms created by the owner
# Query classrooms for the owner and sends to the teacher's template
@app.route('/classroom')
@login_required
def classroom():
    if is_teacher(current_user):
        class_form = ClassroomForm()
        classrooms = session.query(Classroom).filter_by(ClassOwner=current_user.UserIDNumber).all()
        return render_template('classroom.html', classrooms=classrooms, class_form=class_form)
    else:
        render_template('not_allowed.html')


# Classroom Preview
# Takes a classroom id as argument and
# Query the classroom and sends to the preview classroom template
@app.route('/classroom/<int:class_id>')
@login_required
def classroom_preview(class_id):
    cls = session.query(Classroom).filter_by(ClassroomID=class_id).first()
    if cls:
        classroom_owner = session.query(Users).filter_by(UserIDNumber=cls.ClassOwner).first()
        cls_assignments = session.query(Assignment).filter_by(ClassroomID=class_id).all()
        return render_template('preview_classroom.html', classroom=cls, classroomOwner=classroom_owner, cls_assignments=cls_assignments)
    else:
        return 'nothing found'


# HOMEPAGE
@app.route('/')
def home():
    return render_template('index.html')


# Search classroom
# Takes classroom from a form as POST method
@app.route('/search', methods=['GET', 'POST'])
def search_classroom():
    if request.method == "POST":
        classroom_id = request.form['class_id']
        if classroom_id:
            classrm = session.query(Classroom).filter_by(ClassroomID=classroom_id).first()
            if classrm:
                owner = session.query(Users).filter_by(UserIDNumber=classrm.ClassOwner).first()
                return render_template('search_result.html', classrm=classrm, instructor=owner.FullName)
    else:
        return url_for('home')


# ABOUT US PAGE
@app.route('/about')
def about():
    return render_template('about.html')


# CONTACT US PAGE
@app.route('/contact')
def contact():
    return render_template('contact.html')


# Create classroom
# if only the current is a teacher
@app.route('/create_class', methods=['GET', 'POST'])
@login_required
def create_classroom():
    if is_teacher(current_user):
        class_form = ClassroomForm()
        if class_form.validate_on_submit():
            newClass = Classroom(ClassName=class_form.ClassName.data, ClassOwner=current_user.UserIDNumber, ClassDescription=class_form.ClassDescription.data)
            session.add(newClass)
            session.commit()
            flash('Classroom created successfully.')
            return redirect(url_for('dashboard'))
        return render_template('new_classroom.html', class_form=class_form)
    else:
        return render_template('not_allowed.html')


# Finds all classrooms
# Enrolled by the current student
# ad sends to the student_classroom template
@app.route('/student_classrooms')
@login_required
def student_classrooms():
    if not is_teacher(current_user):
        enrollments = session.query(Classroom).join(Enrollment).filter(Classroom.ClassroomID == Enrollment.ClassroomID, Enrollment.UserIDNumber == current_user.UserIDNumber)
        return render_template('student_classroom.html', enrollments=enrollments)
    else:
        return render_template('not_allowed.html')


# Assignment details
# Single assignment preview page
# for students
@app.route('/assignment/<int:class_id>/<int:assignment_id>')
def assignment_details(class_id, assignment_id):
    cls = session.query(Classroom).filter_by(ClassroomID=class_id).first()
    classroom_owner = session.query(Users).filter_by(UserIDNumber=cls.ClassOwner).first()
    asn = session.query(Assignment).filter_by(AssignmentID=assignment_id).first()
    tasks = session.query(Task).filter_by(AssignmentID=asn.AssignmentID).all()
    return render_template('assignment_details.html', cls=cls, asn=asn, tasks=tasks, classroom_owner=classroom_owner)


# Enrollment
# When student enroll classroom
# Takes a classroom id as argument and complete the enrollment
# Stores the classroom id associated with the student id in the
# Enrollment database table.
@app.route('/enroll/<int:classroom_id>')
@login_required
def enroll(classroom_id):
    new_enroll = Enrollment(ClassroomID=classroom_id, UserIDNumber=current_user.UserIDNumber)
    session.add(new_enroll)
    session.commit()
    flash('Successfully enrolled')
    return redirect(url_for('classroom_preview', class_id=classroom_id))


# Reads TXT files
# and Returns the file content as String
def read_file(filename):
    file = open(filename, 'r')
    content = file.read()
    return content


# Reads PDF files
# and Returns the file content as String
def pdf_reader(filename):
    pdfFileObj = open(filename, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    pageObj = pdfReader.getPage(0)
    return pageObj.extractText()


# Assignment dashboard for Teacher
# Query all the class
@app.route('/assignments', methods=['GET', 'POST'])
@app.route('/assignments')
@login_required
def assignments():
    if is_teacher(current_user):
        classes = session.query(Classroom).filter_by(ClassOwner=current_user.UserIDNumber).all()
        if request.method == 'POST':

                name = request.form['name']
                description = request.form['description']
                class_name = request.form['class_name']

                cls = session.query(Classroom).filter_by(ClassName=class_name).first()

                new_assign = Assignment(Name=name, Description=description, OwnerID=current_user.UserIDNumber, ClassroomID=cls.ClassroomID)
                session.add(new_assign)
                session.commit()
                return redirect(url_for('assignments'))

        else:
            assignments_list = session.query(Assignment).filter_by(OwnerID=current_user.UserIDNumber).all()
            return render_template('assignments.html', assignments=assignments_list, classes=classes)
    else:
        return render_template('not_allowed')


@app.route('/assignment_list')
@login_required
def assignment_list():
    assignments_list = session.query(Task).all()
    return render_template('all_assignments.html', assignments=assignments_list)


# Command argument generator
# Takes the input text as input
# and separate input as concatenate
# with 'space' in between inputs
def cmd_generator(input_txt):
    all_inputs = []
    commands = []
    for line in input_txt.split(';'):
        inputs = []
        if not line == '':
            for number in line.split(','):
                inputs.append(number)
            all_inputs.append(inputs)

    for single_input in all_inputs:
        print(single_input)
        cmd = ''
        for i in range(len(single_input)):
            cmd += single_input[i] + ' '
        print(cmd)
        commands.append(cmd)
    return commands


# Output generator from database
# Takes output_txt as input and
# produce outputs as list
def output_generator(output_txt):
    values = []
    for line in output_txt.split(';'):
        if not line == '':
            values.append(line)
    return values

# Calculates the grade
def grade_calculator(correct, items):
    total = 10
    gradePerItem = total / items
    grade = gradePerItem * correct
    return grade

# Store the grade after evaluation
def store_grade(task_id, assignment_id, grade):
    try:
        existing_grade = session.query(Grade).filter_by(TaskID=task_id,AssignmentID=assignment_id).first()
        if not existing_grade:
            new_grade = Grade(StudentID=current_user.UserIDNumber, TaskID=task_id, GradePoint=grade, AssignmentID=assignment_id)
            session.add(new_grade)
            session.commit()
            return True
    except:
        return False



# SOLUTIONS
# Student submit solution
# for a particular assignment ( Single assignment )
@app.route('/submit_solution', methods=['GET', 'POST'])
@login_required
def submit_solution():
    if request.method == "POST":
        c_file = request.files['solutionFile']
        c_file.save('solution.c')

        os.system("gcc solution.c -o solution")

        task_id = int(request.form['task_id'])
        task = session.query(Task).filter_by(TaskID=task_id).first()

        values = cmd_generator(task.Input_TXT)
        grades = 0
        errors = 0
        i = 0
        total_inputs = len(values)
        for value in values:
            cmd = "./solution {}> the_result_{}_.txt".format(value, i)
            os.system(cmd)
            f_name = 'the_result_{}_.txt'.format(i)
            the_result = read_file(f_name)
            the_output = output_generator(task.Output_TXT)

            if int(the_result) == int(the_output[i]):
                grades += 1
            else:
                errors += 1
            i = i + 1
            print('Executed ! ')

        grade = grade_calculator(grades, total_inputs)

        status = store_grade(task.TaskID, task.AssignmentID, grade)
        print(status)

        return render_template('result.html', grade=grade, task=task)

    return render_template('submit_solution.html')

# Shows all classrooms
# All classrooms created by all users
@app.route('/all_classrooms')
@login_required
def all_classrooms():
    classrooms = session.query(Classroom).all()
    return render_template('all_classrooms.html', classrooms=classrooms)


# Assignment Preview
@app.route('/assignment/<int:assignment_id>')
@login_required
def assignment_preview(assignment_id):
    if is_teacher(current_user):
        the_assignment = session.query(Assignment).filter_by(AssignmentID=assignment_id).first()
        tasks = session.query(Task).filter_by(AssignmentID=assignment_id).all()
        return render_template('assignment_preview.html', the_assignment=the_assignment, tasks=tasks)
    return render_template('not_allowed.html')


@app.route('/new_assignment', methods=['GET', 'POST'])
@login_required
def new_assignment():
    if request.method == "POST":
        problemFile = request.files['problemFile']
        inputFile = request.files['inputFile']
        outputFile = request.files['outputFile']
        assign_id = int(request.form['assignment_id'])

        problemFile.save('the_problem.pdf')
        pdf_text = pdf_reader('the_problem.pdf')
        inputFile.save('input.txt')
        input_text = read_file('input.txt')
        outputFile.save('output.txt')
        output_text = read_file('output.txt')

        task = Task(OwnerID=current_user.UserIDNumber, Problem_TXT=pdf_text, Input_TXT=input_text, Output_TXT = output_text, AssignmentID=assign_id)
        session.add(task)
        session.commit()
        return redirect(url_for('assignment_preview', assignment_id=assign_id))

    return render_template('new_assignment.html')


@app.route('/delete_assignment/<int:assignment_id>')
@login_required
def delete_assignment():
    return 'delete assignment function'


def assignment_evaluator():
    return 'hello world!'


# Assignment Evaluator


##################################

# Main Function
if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
