import os
import sys
import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime, Boolean, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from flask_login import UserMixin


Base = declarative_base()


class Users(Base, UserMixin):
    __tablename__ = 'Users'

    UserIDNumber = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    FullName = Column(String(30), nullable=False)
    Username = Column(String(15), nullable=False, unique=True)
    UserType = Column(String(10), nullable=False)
    EmailAddress = Column(String(40), nullable=False)
    Password = Column(String(25), nullable=False)

    def get_id(self):
        return self.UserIDNumber


class Classroom(Base):
    __tablename__ = 'Classroom'

    ClassroomID = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    ClassName = Column(String(100), nullable=False)
    ClassDescription = Column(String(200), nullable=True)
    ClassOwner = Column(Integer, ForeignKey(Users.UserIDNumber))
    Users = relationship(Users)


class Enrollment(Base):
    __tablename__ = 'Enrollment'

    EnrollmentID = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    ClassroomID = Column(Integer, ForeignKey(Classroom.ClassroomID))
    Classroom = relationship(Classroom)
    UserIDNumber = Column(Integer, ForeignKey(Users.UserIDNumber))
    Users = relationship(Users)
    EnrollmentTime = Column(DateTime, default=datetime.datetime.utcnow)


class Assignment(Base):
    __tablename__ = 'Assignment'

    AssignmentID = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    Name = Column(String(100), nullable=False)
    Description = Column(String(500), nullable=True)
    OwnerID = Column(Integer, ForeignKey(Users.UserIDNumber))
    Users = relationship(Users)
    ClassroomID = Column(Integer, ForeignKey(Classroom.ClassroomID))
    Classroom = relationship(Classroom)


class Task(Base):
    __tablename__ = 'Task'

    TaskID = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    OwnerID = Column(Integer, ForeignKey(Users.UserIDNumber))
    Users = relationship(Users)
    Problem_TXT = Column(String(1000), nullable=False)
    Input_TXT = Column(String(200), nullable=False)
    Output_TXT = Column(String(200), nullable=False)
    AssignmentID = Column(Integer, ForeignKey(Assignment.AssignmentID))
    Assignment = relationship(Assignment)


class Grade(Base):
    __tablename__ = 'Grade'

    GradeID = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    StudentID = Column(Integer, ForeignKey(Users.UserIDNumber))
    Users = relationship(Users)
    TaskID = Column(Integer, ForeignKey(Task.TaskID))
    Task = relationship(Task)
    GradePoint = Column(Float, default=0, nullable=False)
    AssignmentID = Column(Integer, ForeignKey(Assignment.AssignmentID))
    Assignment = relationship(Assignment)


# Always stay at the end of the file
engine = create_engine('sqlite:///classroom.db')
Base.metadata.create_all(engine)
