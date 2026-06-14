from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db, login_manager
from app.models import Admin, Student, Teacher, AssessmentEvent, Discipline
from werkzeug.security import check_password_hash

# Создаем Blueprint для основной логики приложения
main_bp = Blueprint('main', __name__)


@login_manager.user_loader
def load_user(user_id):
    user = Admin.query.get(user_id)
    if user:
        return user
    user = Student.query.get(user_id)
    if user:
        return user
    user = Teacher.query.get(user_id)
    if user:
        return user
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
    events = AssessmentEvent.query.join(Student).join(Discipline).order_by(AssessmentEvent.date.desc()).all()
    return render_template('admin_dashboard.html', events=events)


@main_bp.route('/admin/add_assessment', methods=['GET', 'POST'])
@login_required
def add_assessment():
    if request.method == 'POST':
        new_event = AssessmentEvent(
            student_id=request.form.get('student_id'),
            discipline_id=request.form.get('discipline_id'),
            form=request.form.get('form_type'),
            attempt_type=request.form.get('attempt_type'),
            grade=request.form.get('grade'),
            date=request.form.get('date'),
            teacher_id=request.form.get('teacher_id')
        )
        db.session.add(new_event)
        db.session.commit()
        flash('Результат зачётного мероприятия успешно добавлен', 'success')
        return redirect(url_for('main.admin_dashboard'))

    students = Student.query.all()
    disciplines = Discipline.query.all()
    teachers = Teacher.query.all()
    return render_template('add_assessment.html', students=students, disciplines=disciplines, teachers=teachers)


@main_bp.route('/student/dashboard')
@login_required
def student_dashboard():
    events = AssessmentEvent.query.filter_by(student_id=current_user.id).join(Discipline).all()
    return render_template('student_dashboard.html', events=events)


@main_bp.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    return render_template('teacher_dashboard.html')