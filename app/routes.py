from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from sqlalchemy import or_
from app import db, login_manager
from app.models import (
    Admin, Student, Teacher, AssessmentEvent, Discipline, StudyGroup,
    StudyPlan, StudyDirection, Position, Contact, ActionLog,
    TeacherAssignment, PlanDisciplineLink
)
from werkzeug.security import check_password_hash
from collections import defaultdict
import json

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


# Словарь для маппинга имен таблиц в классы моделей
MODELS_MAP = {
    'student': Student,
    'teacher': Teacher,
    'admin_user': Admin, # Используем admin_user, чтобы не конфликтовать с именем Blueprint или переменной
    'study_group': StudyGroup,
    'discipline': Discipline,
    'study_plan': StudyPlan,
    'study_direction': StudyDirection,
    'position': Position,
    'contact': Contact,
    'assessment_event': AssessmentEvent,
    'action_log': ActionLog,
    'teacher_assignment': TeacherAssignment,
    'plan_discipline_link': PlanDisciplineLink
}

# Словарь колонок, по которым разрешен поиск для каждой таблицы
SEARCHABLE_COLUMNS = {
    'student': ['id', 'surname', 'name', 'patronymic', 'student_id_number', 'status'],
    'teacher': ['id', 'surname', 'name', 'patronymic', 'work_email'],
    'admin_user': ['id', 'surname', 'name', 'patronymic', 'work_email'],
    'study_group': ['id', 'number', 'form_of_study', 'current_year', 'current_semester'],
    'discipline': ['id', 'name'],
    'study_plan': ['id', 'approval_year', 'duration_semesters'],
    'study_direction': ['id', 'level', 'code', 'name', 'profile'],
    'position': ['id', 'title', 'rank'],
    'contact': ['id', 'phone', 'email', 'snils'],
    'assessment_event': ['id', 'form', 'attempt_type', 'grade', 'semester'],
    'action_log': ['id', 'operation_type', 'table_name', 'record_id'],
    'teacher_assignment': ['id', 'semester'],
    'plan_discipline_link': ['id', 'semester', 'hours', 'assessment_form']
}

# Словарь для перевода названий колонок на русский язык
COLUMN_NAMES_RU = {
    'id': 'ID',
    'surname': 'Фамилия',
    'name': 'Имя',
    'patronymic': 'Отчество',
    'student_id_number': 'Номер зачётки',
    'status': 'Статус',
    'group_id': 'ID группы',
    'contact_id': 'ID контакта',
    'reg_date': 'Дата регистрации',
    'login': 'Логин',
    'work_email': 'Рабочая почта',
    'position_id': 'ID должности',
    'title': 'Название должности',
    'rank': 'Ранг',
    'permissions_desc': 'Описание прав',
    'level': 'Уровень подготовки',
    'code': 'Код направления',
    'profile': 'Профиль',
    'direction_id': 'ID направления',
    'approval_year': 'Год утверждения',
    'duration_semesters': 'Длительность (сем.)',
    'number': 'Номер группы',
    'form_of_study': 'Форма обучения',
    'current_year': 'Текущий курс',
    'current_semester': 'Текущий семестр',
    'plan_id': 'ID учебного плана',
    'semester': 'Семестр',
    'hours': 'Количество часов',
    'assessment_form': 'Форма контроля',
    'discipline_id': 'ID дисциплины',
    'form': 'Форма аттестации',
    'attempt_type': 'Тип попытки',
    'grade': 'Оценка',
    'date': 'Дата',
    'teacher_id': 'ID преподавателя',
    'operation_type': 'Тип операции',
    'table_name': 'Имя таблицы',
    'record_id': 'ID записи',
    'old_data': 'Старые данные',
    'new_data': 'New данные',
    'passport_series': 'Серия паспорта',
    'passport_number': 'Номер паспорта',
    'passport_dept_code': 'Код подразделения',
    'passport_issue_date': 'Дата выдачи',
    'passport_issued_by': 'Кем выдан',
    'snils': 'СНИЛС',
    'region': 'Субъект РФ',
    'district': 'Район',
    'city': 'Город',
    'street': 'Улица',
    'building': 'Дом',
    'block': 'Корпус',
    'apartment': 'Квартира',
    'postal_code': 'Почтовый индекс',
    'phone': 'Телефон',
    'email': 'Email'
}


@main_bp.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.__class__.__name__ != 'Admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('main.login'))
    return render_template('admin_dashboard.html')


@main_bp.route('/admin/view/<table_name>')
@login_required
def admin_view_table(table_name):
    if current_user.__class__.__name__ != 'Admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('main.login'))

    model = MODELS_MAP.get(table_name)
    if not model:
        abort(404)

    query = model.query
    search_query = request.args.get('search', '').strip()
    search_by = request.args.get('search_by', 'all').strip()  # По умолчанию ищем по всем полям

    # Динамическая фильтрация по поисковому запросу
    if search_query:
        cols_to_search = SEARCHABLE_COLUMNS.get(table_name, ['id'])

        # Если выбран конкретный столбец и он есть в списке разрешенных
        if search_by in cols_to_search:
            col = getattr(model, search_by, None)
            if col is not None:
                if search_by == 'id' and search_query.isdigit():
                    query = query.filter(col == int(search_query))
                elif search_by != 'id':
                    query = query.filter(col.ilike(f'%{search_query}%'))
        else:
            # Если выбрано "Все поля" или передано некорректное значение, ищем по всем разрешенным
            conditions = []
            for col_name in cols_to_search:
                col = getattr(model, col_name, None)
                if col is not None:
                    if col_name == 'id' and search_query.isdigit():
                        conditions.append(col == int(search_query))
                    elif col_name != 'id':
                        conditions.append(col.ilike(f'%{search_query}%'))

            if conditions:
                query = query.filter(or_(*conditions))

    # Пагинация
    page = request.args.get('page', 1, type=int)
    per_page = 15
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # Получаем имена колонок для отображения в таблице (исключаем пароли)
    columns = [col.name for col in model.__table__.columns if 'password' not in col.name]

    # Читаемые названия таблиц для меню
    table_names_ru = {
        'student': 'Студенты', 'teacher': 'Преподаватели', 'admin_user': 'Администраторы',
        'study_group': 'Учебные группы', 'discipline': 'Дисциплины', 'study_plan': 'Учебные планы',
        'study_direction': 'Направления', 'position': 'Должности', 'contact': 'Контакты',
        'assessment_event': 'Зачётные мероприятия', 'action_log': 'Журнал действий',
        'teacher_assignment': 'Нагрузка преподавателей', 'plan_discipline_link': 'План-Дисциплина'
    }

    # Формируем список для выпадающего меню поиска: (значение_в_html, отображаемое_имя)
    searchable_cols_for_dropdown = [('all', 'Все поля')]
    for col in SEARCHABLE_COLUMNS.get(table_name, ['id']):
        ru_name = COLUMN_NAMES_RU.get(col, col.replace('_', ' ').capitalize())
        searchable_cols_for_dropdown.append((col, ru_name))

    return render_template(
        'admin_view_table.html',
        table_name=table_name,
        table_name_ru=table_names_ru.get(table_name, table_name),
        items=pagination.items,
        pagination=pagination,
        columns=columns,
        search_query=search_query,
        search_by=search_by,  # Передаем выбранное поле поиска
        searchable_cols_for_dropdown=searchable_cols_for_dropdown,  # Передаем список для dropdown
        available_tables=MODELS_MAP.keys(),
        table_names_ru=table_names_ru,
        column_names_ru=COLUMN_NAMES_RU
    )


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

            # 1. Проверка на опережение (как мы делали для преподавателя)
            student = Student.query.get(student_id)
            if student and semester > student.group.current_semester:
                flash(
                    f'Ошибка: Нельзя выставлять оценки на опережение. Текущий семестр для группы {student.group.number} — {student.group.current_semester}.',
                    'error')
                return redirect(url_for('main.add_assessment'))

            # 2. Валидация лимита попыток
            unsuccessful_regular_attempts = AssessmentEvent.query.filter(
                AssessmentEvent.student_id == student_id,
                AssessmentEvent.discipline_id == discipline_id,
                AssessmentEvent.attempt_type.in_(['основная', 'первая_пересдача', 'вторая_пересдача']),
                AssessmentEvent.grade.in_(['неудовлетворительно', 'не зачтено', 'неявка'])
            ).count()

            if unsuccessful_regular_attempts >= 3 and attempt_type != 'комиссия':
                flash('Лимит обычных пересдач (3 попытки) исчерпан. Необходимо выбрать тип попытки "комиссия".',
                      'error')
                return redirect(url_for('main.add_assessment'))

            # 3. Преобразование даты и создание записи
            date_str = request.form.get('date')
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

            new_event = AssessmentEvent(
                student_id=student_id,
                discipline_id=discipline_id,
                form=request.form.get('form_type'),
                attempt_type=attempt_type,
                grade=grade,
                date=date_obj,
                semester=semester,
                teacher_id=int(request.form.get('teacher_id'))
            )

            db.session.add(new_event)
            db.session.commit()
            flash('Результат зачётного мероприятия успешно добавлен', 'success')
            # Перенаправляем обратно на просмотр таблицы мероприятий
            return redirect(url_for('main.admin_view_table', table_name='assessment_event'))

        except ValueError:
            flash('Ошибка валидации данных. Проверьте формат даты и числовые поля.', 'error')
            return redirect(url_for('main.add_assessment'))

    # Для GET-запроса: подготовка данных для формы
    students = Student.query.all()
    disciplines = Discipline.query.all()
    teachers = Teacher.query.all()

    max_semesters_display = 8
    if students:
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
    if current_user.__class__.__name__ != 'Teacher':
        flash('Доступ запрещен. Эта страница доступна только преподавателям.', 'error')
        return redirect(url_for('main.login'))

    # 1. Получаем список семестров, в которых у преподавателя есть нагрузка
    assignments_query = db.session.query(TeacherAssignment.semester).filter_by(
        teacher_id=current_user.id
    ).distinct().order_by(TeacherAssignment.semester.desc()).all()

    available_semesters = [a[0] for a in assignments_query]

    requested_semester = request.args.get('semester', type=int)
    if not requested_semester and available_semesters:
        requested_semester = available_semesters[0]
    elif not requested_semester:
        requested_semester = 1

    # 2. Получаем параметры фильтрации (по умолчанию показываем все)
    filter_statuses = request.args.getlist('status')
    if not filter_statuses:
        filter_statuses = ['current', 'past', 'future']

    # 3. Получаем всю нагрузку преподавателя для выбранного семестра
    assignments = TeacherAssignment.query.filter_by(
        teacher_id=current_user.id,
        semester=requested_semester
    ).join(Discipline).join(StudyGroup).order_by(Discipline.name, StudyGroup.number).all()

    # 4. Формируем плоский список с вычислением статуса для фильтрации
    structured_data = []
    for assignment in assignments:
        disc_name = assignment.discipline.name
        group_num = assignment.study_group.number
        group_current_sem = assignment.study_group.current_semester

        # Определяем статус
        if requested_semester > group_current_sem:
            status = 'past'
            status_text = 'Прошедший'
            status_color = '#6c757d'
        elif requested_semester < group_current_sem:
            status = 'future'
            status_text = 'Будущий'
            status_color = '#dc3545'
        else:
            status = 'current'
            status_text = 'Текущий'
            status_color = '#28a745'

        # Пропускаем группу, если её статус не выбран в фильтре
        if status not in filter_statuses:
            continue

        students = Student.query.filter_by(group_id=assignment.group_id, status='учится').order_by(
            Student.surname).all()

        students_with_grades = []
        for student in students:
            all_events = AssessmentEvent.query.filter_by(
                student_id=student.id,
                discipline_id=assignment.discipline_id,
                semester=requested_semester
            ).order_by(AssessmentEvent.date.desc()).all()

            latest_event = all_events[0] if all_events else None
            failing_grades = ['неудовлетворительно', 'не зачтено', 'неявка']
            can_add_grade = not (latest_event and latest_event.grade not in failing_grades)

            students_with_grades.append({
                'student': student,
                'latest_event': latest_event,
                'all_events': all_events,
                'can_add_grade': can_add_grade
            })

        structured_data.append({
            'discipline_name': disc_name,
            'group_num': group_num,
            'status': status,
            'status_text': status_text,
            'status_color': status_color,
            'discipline_id': assignment.discipline.id,
            'group_id': assignment.group_id,
            'students': students_with_grades
        })

    # 5. Логика пагинации
    page = request.args.get('page', 1, type=int)
    per_page = 5  # Количество групп на одной странице
    total_items = len(structured_data)
    total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 1

    # Ограничиваем номер страницы допустимыми значениями
    if page < 1: page = 1
    if page > total_pages: page = total_pages

    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_data = structured_data[start_idx:end_idx]

    # 6. Перегруппировываем отфильтрованные и paginated данные по дисциплинам для шаблона
    grouped_paginated_data = {}
    for item in paginated_data:
        if item['discipline_name'] not in grouped_paginated_data:
            grouped_paginated_data[item['discipline_name']] = []
        grouped_paginated_data[item['discipline_name']].append(item)

    return render_template(
        'teacher_dashboard.html',
        grouped_data=grouped_paginated_data,
        current_semester=requested_semester,
        available_semesters=available_semesters,
        teacher_id=current_user.id,
        filter_statuses=filter_statuses,
        page=page,
        total_pages=total_pages,
        total_items=total_items
    )


@main_bp.route('/api/students/search')
@login_required
def search_students():
    # API для AJAX-поиска студентов по фамилии в конкретной группе
    if current_user.__class__.__name__ not in ['Teacher', 'Admin']:
        return jsonify({'error': 'Доступ запрещен'}), 403

    query = request.args.get('q', '').strip()
    group_id = request.args.get('group_id', type=int)

    if not query or len(query) < 2 or not group_id:
        return jsonify([])

    # Ищем студентов в указанной группе, чья фамилия начинается с введенного текста (или содержит его)
    students = Student.query.filter(
        Student.group_id == group_id,
        Student.status == 'учится',
        db.or_(
            Student.surname.ilike(f'{query}%'),
            Student.surname.ilike(f'% {query}%')
        )
    ).order_by(Student.surname).limit(10).all()

    result = [{'id': s.id, 'name': f'{s.surname} {s.name[0]}.{s.patronymic[0] if s.patronymic else ""}.'} for s in
              students]
    return jsonify(result)


@main_bp.route('/teacher/add_grade', methods=['POST'])
@login_required
def teacher_add_grade():
    if current_user.__class__.__name__ != 'Teacher':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('main.login'))

    try:
        student_id = int(request.form.get('student_id'))
        discipline_id = int(request.form.get('discipline_id'))
        group_id = int(request.form.get('group_id'))
        semester = int(request.form.get('semester'))

        # 1. Проверка нагрузки преподавателя
        assignment = TeacherAssignment.query.filter_by(
            teacher_id=current_user.id,
            discipline_id=discipline_id,
            group_id=group_id,
            semester=semester
        ).first()

        if not assignment:
            flash('Ошибка: у вас нет нагрузки по этой дисциплине в данной группе в этом семестре.', 'error')
            return redirect(url_for('main.teacher_dashboard', semester=semester))

        # 2. Проверка принадлежности студента к группе
        student = Student.query.get(student_id)
        if not student or student.group_id != group_id:
            flash('Ошибка: студент не принадлежит к выбранной группе.', 'error')
            return redirect(url_for('main.teacher_dashboard', semester=semester))

        # 3. Запрет на опережение учебного процесса
        if semester > student.group.current_semester:
            flash(
                f'Ошибка: Нельзя выставлять оценки на опережение. Текущий семестр для группы {student.group.number} — {student.group.current_semester}.',
                'error')
            return redirect(url_for('main.teacher_dashboard', semester=semester))

        # 4. Проверка лимитов попыток (существующий код)
        attempt_type = request.form.get('attempt_type')
        grade = request.form.get('grade')

        unsuccessful_regular_attempts = AssessmentEvent.query.filter(
            AssessmentEvent.student_id == student_id,
            AssessmentEvent.discipline_id == discipline_id,
        AssessmentEvent.attempt_type.in_(['основная', 'первая_пересдача', 'вторая_пересдача']),
        AssessmentEvent.grade.in_(['неудовлетворительно', 'не зачтено', 'неявка'])
        ).count()

        if unsuccessful_regular_attempts >= 3 and attempt_type != 'комиссия':
            flash('Лимит обычных пересдач исчерпан. Необходима комиссионная пересдача.', 'error')
            return redirect(url_for('main.teacher_dashboard', semester=semester))

        # 5. Сохранение (существующий код)
        date_str = request.form.get('date')
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        new_event = AssessmentEvent(
            student_id=student_id,
            discipline_id=discipline_id,
            form=assignment.discipline.name,
            attempt_type=attempt_type,
            grade=grade,
            date=date_obj,
            semester=semester,
            teacher_id=current_user.id
        )

        db.session.add(new_event)
        db.session.commit()
        flash('Оценка успешно сохранена', 'success')

    except ValueError:
        flash('Ошибка валидации данных.', 'error')

    return redirect(url_for('main.teacher_dashboard', semester=request.form.get('semester', type=int)))