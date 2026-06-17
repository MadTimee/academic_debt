from app import db
from datetime import datetime
from flask_login import UserMixin


# 1. Контакт
class Contact(db.Model):
    __tablename__ = 'contact'
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
    __tablename__ = 'position'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    rank = db.Column(db.Integer, nullable=False)
    permissions_mask = db.Column(db.Integer, nullable=False, default=0)
    permissions_desc = db.Column(db.Text, nullable=True)

    admins = db.relationship('Admin', back_populates='position', lazy=True)

    # Вспомогательные методы для работы с правами
    def has_permission(self, table_name):
        """Проверяет, есть ли у должности право на редактирование таблицы"""
        bit = self._get_table_bit(table_name)
        if bit is None:
            return False
        return bool(self.permissions_mask & bit)

    def set_permission(self, table_name, value):
        """Устанавливает право на редактирование таблицы"""
        bit = self._get_table_bit(table_name)
        if bit is None:
            return False

        if value:
            self.permissions_mask |= bit
        else:
            self.permissions_mask &= ~bit
        return True

    @staticmethod
    def _get_table_bit(table_name):
        """Возвращает бит для таблицы"""
        table_bits = {
            'student': 1,
            'teacher': 2,
            'admin_user': 4,
            'study_group': 8,
            'discipline': 16,
            'study_plan': 32,
            'study_direction': 64,
            'position': 128,  # Только для высшего ранга!
            'contact': 256,
            'assessment_event': 512,
            'teacher_assignment': 1024,
            'plan_discipline_link': 2048
        }
        return table_bits.get(table_name)

    @staticmethod
    def get_all_table_bits():
        """Возвращает все биты для отображения в интерфейсе"""
        return {
            'student': {'bit': 1, 'name_ru': 'Студенты'},
            'teacher': {'bit': 2, 'name_ru': 'Преподаватели'},
            'admin_user': {'bit': 4, 'name_ru': 'Администраторы'},
            'study_group': {'bit': 8, 'name_ru': 'Учебные группы'},
            'discipline': {'bit': 16, 'name_ru': 'Дисциплины'},
            'study_plan': {'bit': 32, 'name_ru': 'Учебные планы'},
            'study_direction': {'bit': 64, 'name_ru': 'Направления'},
            'position': {'bit': 128, 'name_ru': 'Должности'},
            'contact': {'bit': 256, 'name_ru': 'Контакты'},
            'assessment_event': {'bit': 512, 'name_ru': 'Зачётные мероприятия'},
            'teacher_assignment': {'bit': 1024, 'name_ru': 'Нагрузка преподавателей'},
            'plan_discipline_link': {'bit': 2048, 'name_ru': 'Связь план-дисциплина'}
        }

    def get_permissions_list(self):
        """Возвращает список прав для отображения"""
        all_bits = self.get_all_table_bits()
        result = {}
        for table_name, info in all_bits.items():
            result[table_name] = {
                'name_ru': info['name_ru'],
                'has_permission': bool(self.permissions_mask & info['bit']),
                'bit': info['bit']
            }
        return result


# 3. Направление подготовки
class StudyDirection(db.Model):
    __tablename__ = 'study_direction'
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(50))
    code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    profile = db.Column(db.String(255))

    plans = db.relationship('StudyPlan', back_populates='direction', lazy=True)


# 4. Учебный план
class StudyPlan(db.Model):
    __tablename__ = 'study_plan'
    id = db.Column(db.Integer, primary_key=True)
    direction_id = db.Column(db.Integer, db.ForeignKey('study_direction.id'), nullable=False)
    approval_year = db.Column(db.Integer, nullable=False)
    duration_semesters = db.Column(db.Integer, nullable=False)

    direction = db.relationship('StudyDirection', back_populates='plans')
    groups = db.relationship('StudyGroup', back_populates='plan', lazy=True)
    disciplines_link = db.relationship(
        'PlanDisciplineLink',
        back_populates='plan',
        lazy=True
    )


# 5. Учебная группа
class StudyGroup(db.Model):
    __tablename__ = 'study_group'
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('study_plan.id'), nullable=False)
    form_of_study = db.Column(db.String(50))
    current_year = db.Column(db.Integer)
    current_semester = db.Column(db.Integer, nullable=False, default=1)

    plan = db.relationship('StudyPlan', back_populates='groups')
    students = db.relationship(
        'Student',
        back_populates='group',
        lazy=True,
        cascade='all, delete-orphan'
    )
    teacher_assignments = db.relationship(
        'TeacherAssignment',
        back_populates='study_group',
        lazy=True,
        cascade='all, delete-orphan'
    )


# 6. Дисциплина
class Discipline(db.Model):
    __tablename__ = 'discipline'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    plans_link = db.relationship('PlanDisciplineLink', back_populates='discipline', lazy=True)
    teacher_assignments = db.relationship('TeacherAssignment', back_populates='discipline', lazy=True)
    assessments = db.relationship(
        'AssessmentEvent',
        back_populates='discipline',
        lazy=True
    )


# 7. Связь План-Дисциплина
class PlanDisciplineLink(db.Model):
    __tablename__ = 'plan_discipline_link'
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('study_plan.id'), nullable=False)
    discipline_id = db.Column(db.Integer, db.ForeignKey('discipline.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    hours = db.Column(db.Integer, nullable=False)
    assessment_form = db.Column(db.String(50))

    plan = db.relationship('StudyPlan', back_populates='disciplines_link')
    discipline = db.relationship('Discipline', back_populates='plans_link')


# 8. Студент
class Student(db.Model, UserMixin):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    surname = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    patronymic = db.Column(db.String(100))
    student_id_number = db.Column(db.String(50), unique=True, nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('study_group.id'), nullable=False)
    status = db.Column(db.String(50), default='учится')
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id', ondelete='CASCADE'), unique=True)
    reg_date = db.Column(db.Date, default=datetime.utcnow)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    group = db.relationship('StudyGroup', back_populates='students')
    assessments = db.relationship(
        'AssessmentEvent',
        back_populates='student',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def get_id(self):
        return f"student_{self.id}"


# 9. Преподаватель
class Teacher(db.Model, UserMixin):
    __tablename__ = 'teacher'
    id = db.Column(db.Integer, primary_key=True)
    surname = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    patronymic = db.Column(db.String(100))
    work_email = db.Column(db.String(100), unique=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id', ondelete='CASCADE'), unique=True)
    reg_date = db.Column(db.Date, default=datetime.utcnow)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    assignments = db.relationship(
        'TeacherAssignment',
        back_populates='teacher',
        lazy=True,
        cascade='all, delete-orphan'
    )
    assessments = db.relationship(
        'AssessmentEvent',
        back_populates='teacher',
        lazy=True
    )

    def get_id(self):
        return f"teacher_{self.id}"


# 10. Администратор
class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    surname = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    patronymic = db.Column(db.String(100))
    position_id = db.Column(db.Integer, db.ForeignKey('position.id'), nullable=False)
    work_email = db.Column(db.String(100), unique=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id', ondelete='CASCADE'), unique=True)
    reg_date = db.Column(db.Date, default=datetime.utcnow)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    position = db.relationship('Position', back_populates='admins')
    actions = db.relationship('ActionLog', back_populates='admin', lazy=True)

    def get_id(self):
        return f"admin_{self.id}"


# 11. Зачётное мероприятие
class AssessmentEvent(db.Model):
    __tablename__ = 'assessment_event'
    id = db.Column(db.Integer, primary_key=True)
    discipline_id = db.Column(db.Integer, db.ForeignKey('discipline.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    form = db.Column(db.String(50), nullable=False)
    attempt_type = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    grade = db.Column(db.String(50))
    semester = db.Column(db.Integer, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id', ondelete='SET NULL'), nullable=True)

    discipline = db.relationship('Discipline', back_populates='assessments')
    student = db.relationship('Student', back_populates='assessments')
    teacher = db.relationship('Teacher', back_populates='assessments')


# 12. Действие (Журнал аудита)
class ActionLog(db.Model):
    __tablename__ = 'action_log'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id', ondelete='SET NULL'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    operation_type = db.Column(db.String(10), nullable=False)
    table_name = db.Column(db.String(100), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    old_data = db.Column(db.Text, nullable=True)
    new_data = db.Column(db.Text, nullable=True)

    admin = db.relationship('Admin', back_populates='actions')


# 13. Распределение нагрузки преподавателя (Новая сущность)
class TeacherAssignment(db.Model):
    __tablename__ = 'teacher_assignment'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    discipline_id = db.Column(db.Integer, db.ForeignKey('discipline.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('study_group.id'), nullable=False)
    semester = db.Column(db.Integer, nullable=False)

    # Явные двусторонние связи через back_populates
    teacher = db.relationship('Teacher', back_populates='assignments')
    discipline = db.relationship('Discipline', back_populates='teacher_assignments')
    study_group = db.relationship('StudyGroup', back_populates='teacher_assignments')