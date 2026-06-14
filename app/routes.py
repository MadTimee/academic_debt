from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from app import db, login_manager
from app.models import Admin, Student, Teacher, AssessmentEvent, Discipline
from werkzeug.security import check_password_hash

main_bp = Blueprint('main', __name__)


@login_manager.user_loader
def load_user(user_id_str):
    if user_id_str.startswith("admin_"):
        return Admin.query.get(int(user_id_str.split("_")[1]))
    elif user_id_str.startswith("student_"):
        return Student.query.get(int(user_id_str.split("_")[1]))
    elif user_id_str.startswith("teacher_"):
        return Teacher.query.get(int(user_id_str.split("_")[1]))
    return None


@main_bp.route('/')
def index():
    return redirect(url_for('main.login'))


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('login')
        password = request.form.get('password')

        user = Admin.query.filter_by(login=login_input).first()
        role = 'admin'
        if not user:
            user = Student.query.filter_by(login=login_input).first()
            role = 'student'
        if not user:
            user = Teacher.query.filter_by(login=login_input).first()
            role = 'teacher'

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if role == 'admin':
                return redirect(url_for('main.admin_dashboard'))
            elif role == 'teacher':
                return redirect(url_for('main.teacher_dashboard'))
            else:
                return redirect(url_for('main.student_dashboard'))
        else:
            flash('Неверный логин или пароль', 'error')

    return render_template('login.html')


@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))


@main_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Проверка роли: доступ только для Администратора
    if current_user.__class__.__name__ != 'Admin':
        flash('Доступ запрещен. Эта страница доступна только сотрудникам деканата.', 'error')
        return redirect(url_for('main.login'))

    events = AssessmentEvent.query.join(Student).join(Discipline).order_by(AssessmentEvent.date.desc()).all()
    return render_template('admin_dashboard.html', events=events)


@main_bp.route('/admin/add_assessment', methods=['GET', 'POST'])
@login_required
def add_assessment():
    if current_user.__class__.__name__ != 'Admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        try:
            date_str = request.form.get('date')
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

            new_event = AssessmentEvent(
                student_id=int(request.form.get('student_id')),
                discipline_id=int(request.form.get('discipline_id')),
                form=request.form.get('form_type'),
                attempt_type=request.form.get('attempt_type'),
                grade=request.form.get('grade'),
                date=date_obj,
                teacher_id=int(request.form.get('teacher_id'))
            )

            db.session.add(new_event)
            db.session.commit()
            flash('Результат зачётного мероприятия успешно добавлен', 'success')
            return redirect(url_for('main.admin_dashboard'))

        except ValueError:
            flash('Ошибка валидации данных. Проверьте формат даты и числовые поля.', 'error')
            return redirect(url_for('main.add_assessment'))

    students = Student.query.all()
    disciplines = Discipline.query.all()
    teachers = Teacher.query.all()
    return render_template('add_assessment.html', students=students, disciplines=disciplines, teachers=teachers)


@main_bp.route('/student/dashboard')
@login_required
def student_dashboard():
    # Проверка роли: доступ только для Студента
    if current_user.__class__.__name__ != 'Student':
        flash('Доступ запрещен. Эта страница доступна только студентам.', 'error')
        return redirect(url_for('main.login'))

    events = AssessmentEvent.query.filter_by(student_id=current_user.id).join(Discipline).all()
    return render_template('student_dashboard.html', events=events)


@main_bp.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    # Проверка роли: доступ только для Преподавателя
    if current_user.__class__.__name__ != 'Teacher':
        flash('Доступ запрещен. Эта страница доступна только преподавателям.', 'error')
        return redirect(url_for('main.login'))

    return render_template('teacher_dashboard.html')