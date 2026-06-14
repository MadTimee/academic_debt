from app import db
from datetime import datetime
from flask_login import UserMixin

# 1. Контакт
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    passport_series = db.Column(db.String(4))
    passport_number = db.Column(db.String(6))
    passport_dept_code = db.Column(db.String(7))
    passport_issue_date = db.Column(db.Date)
    passport_issued_by = db.Column(db.String(255))
    snils = db.Column(db.String(11))
    region = db.Column(db.String(100))
    district = db.Column(db.String(100))
    city = db.Column(db.String(100))
    street = db.Column(db.String(100))
    building = db.Column(db.String(10))
    block = db.Column(db.String(10), nullable=True)
    apartment = db.Column(db.String(10))
    postal_code = db.Column(db.String(6))
    phone = db.Column(db.String(15))
    email = db.Column(db.String(100))

# 2. Должность
class Position(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    rank = db.Column(db.Integer, nullable=False) # 1-5 для иерархии прав
    permissions_desc = db.Column(db.Text, nullable=True)
    admins = db.relationship('Admin', backref='position', lazy=True)

# 3. Направление подготовки
class StudyDirection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(50)) # бакалавриат, магистратура
    code = db.Column(db.String(20), nullable=False) # например, 02.03.01
    name = db.Column(db.String(255), nullable=False)
    profile = db.Column(db.String(255))
    plans = db.relationship('StudyPlan', backref='direction', lazy=True)

# 4. Учебный план
class StudyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    direction_id = db.Column(db.Integer, db.ForeignKey('study_direction.id'), nullable=False)
    approval_year = db.Column(db.Integer, nullable=False)
    duration_semesters = db.Column(db.Integer, nullable=False)
    groups = db.relationship('StudyGroup', backref='plan', lazy=True)
    disciplines_link = db.relationship('PlanDisciplineLink', backref='plan', lazy=True, cascade='all, delete-orphan')

# 5. Учебная группа
class StudyGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), nullable=False) # например, 0292-04
    plan_id = db.Column(db.Integer, db.ForeignKey('study_plan.id'), nullable=False)
    form_of_study = db.Column(db.String(50)) # очная, заочная
    current_year = db.Column(db.Integer)
    students = db.relationship('Student', backref='group', lazy=True)

# 6. Дисциплина
class Discipline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    plans_link = db.relationship('PlanDisciplineLink', backref='discipline', lazy=True)
    assessments = db.relationship('AssessmentEvent', backref='discipline', lazy=True)

# 7. Связь План-Дисциплина (Many-to-Many)
class PlanDisciplineLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('study_plan.id'), nullable=False)
    discipline_id = db.Column(db.Integer, db.ForeignKey('discipline.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    hours = db.Column(db.Integer, nullable=False)
    assessment_form = db.Column(db.String(50)) # зачет, экзамен

# 8. Студент
class Student(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    surname = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    patronymic = db.Column(db.String(100))
    student_id_number = db.Column(db.String(50), unique=True, nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('study_group.id'), nullable=False)
    status = db.Column(db.String(50), default='учится')
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), unique=True)
    reg_date = db.Column(db.Date, default=datetime.utcnow)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    assessments = db.relationship('AssessmentEvent', backref='student', lazy=True)

    def get_id(self):
        return f"student_{self.id}"

# 9. Преподаватель
class Teacher(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    surname = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    patronymic = db.Column(db.String(100))
    work_email = db.Column(db.String(100), unique=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), unique=True)
    reg_date = db.Column(db.Date, default=datetime.utcnow)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    assessments = db.relationship('AssessmentEvent', backref='teacher', lazy=True)

    def get_id(self):
        return f"teacher_{self.id}"

# 10. Администратор
class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    surname = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    patronymic = db.Column(db.String(100))
    position_id = db.Column(db.Integer, db.ForeignKey('position.id'), nullable=False)
    work_email = db.Column(db.String(100), unique=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), unique=True)
    reg_date = db.Column(db.Date, default=datetime.utcnow)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    actions = db.relationship('ActionLog', backref='admin', lazy=True)

    def get_id(self):
        return f"admin_{self.id}"

# 11. Зачётное мероприятие
class AssessmentEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discipline_id = db.Column(db.Integer, db.ForeignKey('discipline.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    form = db.Column(db.String(50), nullable=False)
    attempt_type = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    grade = db.Column(db.String(50))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)

# 12. Действие (Журнал аудита)
class ActionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    operation_type = db.Column(db.String(10), nullable=False) # INSERT, UPDATE, DELETE
    table_name = db.Column(db.String(100), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    old_data = db.Column(db.Text, nullable=True) # JSON строка
    new_data = db.Column(db.Text, nullable=True) # JSON строка