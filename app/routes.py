from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from app import db, login_manager
from app.models import Admin, Student, Teacher, AssessmentEvent, Discipline
from werkzeug.security import check_password_hash
from collections import defaultdict

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
            student_id = int(request.form.get('student_id'))
            discipline_id = int(request.form.get('discipline_id'))
            attempt_type = request.form.get('attempt_type')
            grade = request.form.get('grade')
            semester = int(request.form.get('semester'))

            # 1. Получаем студента и его учебный план для валидации семестра
            student = Student.query.get(student_id)
            if not student:
                flash('Ошибка: студент не найден', 'error')
                return redirect(url_for('main.add_assessment'))

            max_semesters = student.group.plan.duration_semesters

            # 2. Валидация семестра
            if semester < 1 or semester > max_semesters:
                flash(
                    f'Ошибка: указан некорректный семестр. Максимальное количество семестров для группы {student.group.number} составляет {max_semesters}.',
                    'error')
                return redirect(url_for('main.add_assessment'))

            # 3. Валидация лимита попыток (как было ранее)
            unsuccessful_regular_attempts = AssessmentEvent.query.filter(
                AssessmentEvent.student_id == student_id,
                AssessmentEvent.discipline_id == discipline_id,
                AssessmentEvent.attempt_type.in_(['основная', 'первая_пересдача', 'вторая_пересдача']),
                AssessmentEvent.grade.in_(['неудовлетворительно', 'не зачтено', 'неявка'])
            ).count()

            if unsuccessful_regular_attempts >= 3 and attempt_type != 'комиссия':
                flash(
                    'Лимит обычных пересдач (3 попытки: основная + 2 пересдачи) исчерпан. Для данной дисциплины необходимо выбрать тип попытки "комиссия".',
                    'error')
                return redirect(url_for('main.add_assessment'))

            # 4. Преобразуем строку даты в объект datetime.date
            date_str = request.form.get('date')
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

            # 5. Создаем объект мероприятия
            new_event = AssessmentEvent(
                student_id=student_id,
                discipline_id=discipline_id,
                form=request.form.get('form_type'),
                attempt_type=attempt_type,
                grade=grade,
                date=date_obj,
                semester=semester,  # <-- Используем провалидированный семестр
                teacher_id=int(request.form.get('teacher_id'))
            )

            db.session.add(new_event)
            db.session.commit()
            flash('Результат зачётного мероприятия успешно добавлен', 'success')
            return redirect(url_for('main.admin_dashboard'))

        except ValueError:
            flash('Ошибка валидации данных. Проверьте формат даты и числовые поля.', 'error')
            return redirect(url_for('main.add_assessment'))

    # Для GET-запроса: определяем максимальный семестр для отображения в выпадающем списке
    # Берем максимальное значение duration_semesters среди всех учебных планов в системе
    students = Student.query.all()
    disciplines = Discipline.query.all()
    teachers = Teacher.query.all()

    max_semesters_display = 8  # Значение по умолчанию
    if students:
        # Находим максимальную продолжительность среди всех планов, привязанных к текущим студентам
        max_semesters_display = max([s.group.plan.duration_semesters for s in students])

    return render_template(
        'add_assessment.html',
        students=students,
        disciplines=disciplines,
        teachers=teachers,
        max_semesters_display=max_semesters_display
    )


@main_bp.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.__class__.__name__ != 'Student':
        flash('Доступ запрещен. Эта страница доступна только студентам.', 'error')
        return redirect(url_for('main.login'))

    # Получаем максимальное количество семестров из учебного плана группы текущего студента
    max_semesters = current_user.group.plan.duration_semesters

    # 1. Определяем, какие семестры вообще есть у этого студента в базе
    semesters_query = db.session.query(AssessmentEvent.semester).filter_by(
        student_id=current_user.id
    ).distinct().order_by(AssessmentEvent.semester.asc()).all()

    available_semesters = [s[0] for s in semesters_query]

    # 2. Определяем текущий запрашиваемый семестр
    requested_semester = request.args.get('semester', type=int)
    if not requested_semester and available_semesters:
        requested_semester = available_semesters[-1]
    elif not requested_semester:
        requested_semester = 1

        # 3. Получаем все оценки за выбранный семестр
    events = AssessmentEvent.query.filter_by(
        student_id=current_user.id,
        semester=requested_semester
    ).join(Discipline).order_by(Discipline.name, AssessmentEvent.date.desc()).all()

    # 4. Группируем события по названию дисциплины
    grouped_events = defaultdict(list)
    for event in events:
        grouped_events[event.discipline.name].append(event)

    return render_template(
        'student_dashboard.html',
        grouped_events=grouped_events,
        current_semester=requested_semester,
        available_semesters=available_semesters,
        max_semesters=max_semesters
    )


@main_bp.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    # Проверка роли: доступ только для Преподавателя
    if current_user.__class__.__name__ != 'Teacher':
        flash('Доступ запрещен. Эта страница доступна только преподавателям.', 'error')
        return redirect(url_for('main.login'))

    return render_template('teacher_dashboard.html')