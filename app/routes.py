from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, date
from sqlalchemy import or_, func
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
    'student': ['id', 'fio', 'student_id_number', 'status'],
    'teacher': ['id', 'fio', 'work_email'],
    'admin_user': ['id', 'fio', 'work_email'],
    'study_group': ['id', 'number', 'form_of_study', 'current_year', 'current_semester'],
    'discipline': ['id', 'name'],
    'study_plan': ['id', 'approval_year', 'duration_semesters'],
    'study_direction': ['id', 'level', 'code', 'name', 'profile'],
    'position': ['id', 'title', 'rank'],
    'contact': ['id', 'phone', 'email', 'snils'],
    'assessment_event': ['id', 'form', 'attempt_type', 'grade', 'semester', 'date'],
    'action_log': ['id', 'operation_type', 'table_name', 'record_id', 'timestamp'],
    'teacher_assignment': ['id', 'semester'],
    'plan_discipline_link': ['id', 'semester', 'hours', 'assessment_form']
}

# Словарь для перевода названий колонок на русский язык
COLUMN_NAMES_RU = {
    'id': 'ID',
    'fio': 'ФИО',
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
    'permissions_mask': 'Права доступа',
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
    'new_data': 'Новые данные',
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
    'email': 'Email',
    'timestamp': 'Дата и время',
    'admin_id': 'ID администратора',
    'student_id': 'ID студента'
}


def check_edit_permission(table_name):
    """Проверяет, есть ли у текущего администратора право на редактирование таблицы"""
    if current_user.__class__.__name__ != 'Admin':
        return False

    # Системный администратор (rank=5) имеет все права
    if current_user.position.rank == 5:
        return True

    # Проверяем право на редактирование конкретной таблицы
    return current_user.position.has_permission(table_name)


def check_position_edit_permission(position_id=None):
    """Специальная проверка для редактирования должностей"""
    if current_user.__class__.__name__ != 'Admin':
        return False

    # Только пользователи с rank=5 могут редактировать должности
    if current_user.position.rank != 5:
        return False

    # Если передан ID должности, проверяем, что это не должность с rank=5
    if position_id:
        position = Position.query.get(position_id)
        if position and position.rank == 5:
            # Нельзя редактировать должность с максимальным рангом
            return False

    return True


def check_position_delete_permission(position_id):
    """Специальная проверка для удаления должностей"""
    if current_user.__class__.__name__ != 'Admin':
        return False

    # Только пользователи с rank=5 могут удалять должности
    if current_user.position.rank != 5:
        return False

    # Проверяем, что это не должность с rank=5
    position = Position.query.get(position_id)
    if position and position.rank == 5:
        # Нельзя удалять должность с максимальным рангом
        return False

    # Проверяем, что есть хотя бы один администратор с этой должностью
    admin_count = Admin.query.filter_by(position_id=position_id).count()
    if admin_count > 0:
        # Нельзя удалять должность, если есть администраторы с ней
        return False

    return True


def log_action(admin_id, operation_type, table_name, record_id, old_data=None, new_data=None):
    """Создает запись в журнале аудита"""
    # Для UPDATE операций сохраняем только diff
    if operation_type == 'UPDATE' and old_data and new_data:
        diff = get_diff(old_data, new_data)
        # Если изменений нет, не логируем
        if not diff:
            return
        # Сохраняем только измененные поля
        old_data = diff
        # new_data тоже сохраняем как diff для единообразия
        new_data = diff

    action = ActionLog(
        admin_id=admin_id,
        operation_type=operation_type,
        table_name=table_name,
        record_id=record_id,
        old_data=json.dumps(old_data, ensure_ascii=False, default=str) if old_data else None,
        new_data=json.dumps(new_data, ensure_ascii=False, default=str) if new_data else None
    )
    db.session.add(action)
    db.session.commit()


def get_record_data(record, columns):
    """Извлекает данные записи для логирования"""
    data = {}
    for col in columns:
        value = getattr(record, col, None)
        if isinstance(value, datetime):
            value = value.isoformat()
        elif isinstance(value, date):
            value = value.isoformat()
        data[col] = value
    return data


def get_diff(old_data, new_data):
    """Возвращает только измененные поля"""
    diff = {}
    for key in new_data.keys():
        old_value = old_data.get(key)
        new_value = new_data.get(key)
        # Сравниваем значения
        if old_value != new_value:
            diff[key] = {
                'old': old_value,
                'new': new_value
            }
    return diff


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
    search_by = request.args.get('search_by', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    # 1. Динамически получаем список колонок для отображения (исключая пароли)
    columns = [col.name for col in model.__table__.columns if 'password' not in col.name]

    # 2. Определяем, есть ли в таблице колонки с датами
    date_columns = [col.name for col in model.__table__.columns
                    if col.name in ['date', 'reg_date', 'passport_issue_date', 'timestamp']]
    has_date_column = len(date_columns) > 0

    # 3. Определяем, по какой колонке ищем
    if not search_by or search_by not in columns:
        search_by = columns[0] if columns else 'id'

    # 4. Применяем фильтр по текстовому поиску
    if search_query:
        conditions = []
        cols_to_search = SEARCHABLE_COLUMNS.get(table_name, ['id'])

        for col_name in cols_to_search:
            if col_name == 'fio':
                surname_col = getattr(model, 'surname', None)
                name_col = getattr(model, 'name', None)
                patronymic_col = getattr(model, 'patronymic', None)

                if surname_col and name_col:
                    fio_expr = func.trim(
                        func.coalesce(surname_col, '') + ' ' +
                        func.coalesce(name_col, '') + ' ' +
                        func.coalesce(patronymic_col, '')
                    )
                    conditions.append(fio_expr.ilike(f'%{search_query}%'))

            elif col_name in ['date', 'reg_date', 'passport_issue_date', 'timestamp']:
                if not date_from and not date_to:
                    col = getattr(model, col_name, None)
                    if col is not None:
                        formatted_date_col = func.strftime('%d.%m.%Y', col)
                        conditions.append(formatted_date_col.ilike(f'%{search_query}%'))

            else:
                col = getattr(model, col_name, None)
                if col is not None:
                    if col_name == 'id' and search_query.isdigit():
                        conditions.append(col == int(search_query))
                    elif col_name != 'id':
                        conditions.append(col.ilike(f'%{search_query}%'))

        if conditions:
            query = query.filter(or_(*conditions))

    # 5. Применяем фильтр по датам
    if has_date_column and (date_from or date_to):
        date_col_name = date_columns[0]
        date_col = getattr(model, date_col_name)

        def parse_date_part(date_str):
            parts = date_str.split('.')
            if len(parts) == 3:
                day, month, year = parts
                if day.isdigit() and month.isdigit() and year.isdigit():
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            elif len(parts) == 2:
                month, year = parts
                if month.isdigit() and year.isdigit():
                    return f"{year}-{month.zfill(2)}"
            elif len(parts) == 1:
                year = parts[0]
                if year.isdigit():
                    return year
            return None

        if date_from:
            parsed_from = parse_date_part(date_from)
            if parsed_from:
                query = query.filter(date_col >= parsed_from)

        if date_to:
            parsed_to = parse_date_part(date_to)
            if parsed_to:
                if len(parsed_to) == 10:
                    query = query.filter(date_col <= parsed_to)
                elif len(parsed_to) == 7:
                    query = query.filter(date_col <= parsed_to + '-31')
                elif len(parsed_to) == 4:
                    query = query.filter(date_col <= parsed_to + '-12-31')

    # 6. Пагинация
    page = request.args.get('page', 1, type=int)
    per_page = 15
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 7. Проверка прав на редактирование
    if table_name == 'position':
        can_edit = check_position_edit_permission()
    else:
        can_edit = check_edit_permission(table_name)

    table_names_ru = {
        'student': 'Студенты', 'teacher': 'Преподаватели', 'admin_user': 'Администраторы',
        'study_group': 'Учебные группы', 'discipline': 'Дисциплины', 'study_plan': 'Учебные планы',
        'study_direction': 'Направления', 'position': 'Должности', 'contact': 'Контакты',
        'assessment_event': 'Зачётные мероприятия', 'action_log': 'Журнал действий',
        'teacher_assignment': 'Нагрузка преподавателей', 'plan_discipline_link': 'План-Дисциплина'
    }

    searchable_cols_for_dropdown = []
    for col in columns:
        if col in ['surname', 'name', 'patronymic']:
            continue
        ru_name = COLUMN_NAMES_RU.get(col, col.replace('_', ' ').capitalize())
        searchable_cols_for_dropdown.append((col, ru_name))

    if 'fio' not in [c[0] for c in searchable_cols_for_dropdown] and hasattr(model, 'surname') and hasattr(model,
                                                                                                           'name'):
        searchable_cols_for_dropdown.insert(1, ('fio', 'ФИО'))

    return render_template(
        'admin_view_table.html',
        table_name=table_name,
        table_name_ru=table_names_ru.get(table_name, table_name),
        items=pagination.items,
        pagination=pagination,
        columns=columns,
        search_query=search_query,
        search_by=search_by,
        date_from=date_from,
        date_to=date_to,
        has_date_column=has_date_column,
        can_edit=can_edit,
        searchable_cols_for_dropdown=searchable_cols_for_dropdown,
        available_tables=MODELS_MAP.keys(),
        table_names_ru=table_names_ru,
        column_names_ru=COLUMN_NAMES_RU
    )


@main_bp.route('/admin/delete/<table_name>/<int:record_id>', methods=['POST'])
@login_required
def admin_delete_record(table_name, record_id):
    """Удаляет запись из указанной таблицы"""
    if current_user.__class__.__name__ != 'Admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('main.admin_dashboard'))

    # Проверяем право на удаление
    if table_name == 'position':
        if not check_position_delete_permission(record_id):
            flash('Нельзя удалить должность с максимальным рангом или должность, за которой закреплены администраторы.',
                  'error')
            return redirect(url_for('main.admin_view_table', table_name=table_name))
    else:
        if not check_edit_permission(table_name):
            flash(f'У вас нет прав на удаление записей в таблице "{table_name}".', 'error')
            return redirect(url_for('main.admin_view_table', table_name=table_name))

    model = MODELS_MAP.get(table_name)
    if not model:
        abort(404)

    record = model.query.get(record_id)
    if not record:
        flash('Запись не найдена.', 'error')
        return redirect(url_for('main.admin_view_table', table_name=table_name))

    # Специальная обработка для разных таблиц
    if table_name == 'teacher':
        return delete_teacher(record, record_id)

    if table_name == 'student':
        return delete_student(record, record_id)

    if table_name == 'discipline':
        return delete_discipline(record, record_id)

    if table_name == 'study_group':
        return delete_study_group(record, record_id)

    if table_name == 'study_plan':
        return delete_study_plan(record, record_id)

    if table_name == 'study_direction':
        return delete_study_direction(record, record_id)

    if table_name == 'position':
        return delete_position(record, record_id)

    if table_name == 'contact':
        return delete_contact(record, record_id)

    if table_name == 'admin_user':
        return delete_admin_user(record, record_id)

    # Для остальных таблиц - общая логика с проверкой зависимостей
    dependencies = check_dependencies(table_name, record_id)
    force_delete = request.form.get('force_delete') == 'true'

    if dependencies and not force_delete:
        dep_list = ', '.join(dependencies)
        flash(
            f'Внимание! Удаление этой записи также удалит связанные данные: {dep_list}. Нажмите "Удалить с зависимостями" для подтверждения.',
            'warning')
        return redirect(url_for('main.admin_view_table', table_name=table_name, show_delete_warning=record_id))

    columns = [col.name for col in model.__table__.columns if 'password' not in col.name]
    old_data = get_record_data(record, columns)

    try:
        db.session.delete(record)
        db.session.commit()

        log_action(
            admin_id=current_user.id,
            operation_type='DELETE',
            table_name=table_name,
            record_id=record_id,
            old_data=old_data
        )

        if dependencies:
            flash('Запись и связанные с ней данные успешно удалены.', 'success')
        else:
            flash('Запись успешно удалена.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'error')

    return redirect(url_for('main.admin_view_table', table_name=table_name))


def delete_student(student, student_id):
    """Специальная обработка удаления студента"""
    try:
        # 1. Сохраняем ID контакта для последующего удаления
        contact_id = student.contact_id

        # 2. Удаляем студента (вместе с оценками через каскад)
        db.session.delete(student)
        db.session.commit()

        # 3. Удаляем контакт, если он был
        if contact_id:
            contact = Contact.query.get(contact_id)
            if contact:
                db.session.delete(contact)
                db.session.commit()

        log_action(
            admin_id=current_user.id,
            operation_type='DELETE',
            table_name='student',
            record_id=student_id,
            old_data={'surname': student.surname, 'name': student.name, 'student_id_number': student.student_id_number}
        )

        flash('Студент успешно удален. Все оценки студента удалены.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении студента: {str(e)}', 'error')

    return redirect(url_for('main.admin_view_table', table_name='student'))


def delete_teacher(teacher, teacher_id):
    """Специальная обработка удаления преподавателя"""
    try:
        # 1. Сохраняем ID контакта для последующего удаления
        contact_id = teacher.contact_id

        # 2. Удаляем нагрузку преподавателя (TeacherAssignment) - через каскад
        # 3. Обнуляем teacher_id в AssessmentEvent (уже настроено через ondelete='SET NULL')
        #    Это произойдет автоматически благодаря внешнему ключу

        # 4. Удаляем самого преподавателя
        db.session.delete(teacher)
        db.session.commit()

        # 5. Удаляем контакт, если он был
        if contact_id:
            contact = Contact.query.get(contact_id)
            if contact:
                db.session.delete(contact)
                db.session.commit()

        log_action(
            admin_id=current_user.id,
            operation_type='DELETE',
            table_name='teacher',
            record_id=teacher_id,
            old_data={'surname': teacher.surname, 'name': teacher.name, 'id': teacher.id}
        )

        flash('Преподаватель успешно удален. Оценки, выставленные преподавателем, сохранены.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении преподавателя: {str(e)}', 'error')

    return redirect(url_for('main.admin_view_table', table_name='teacher'))


def delete_discipline(discipline, discipline_id):
    """Специальная обработка удаления дисциплины"""
    try:
        # Проверяем наличие оценок
        assessments_count = AssessmentEvent.query.filter_by(discipline_id=discipline.id).count()
        if assessments_count > 0:
            flash(f'Невозможно удалить дисциплину "{discipline.name}", так как по ней есть {assessments_count} оценок.',
                  'error')
            return redirect(url_for('main.admin_view_table', table_name='discipline'))

        # Проверяем наличие в учебных планах
        plans_count = PlanDisciplineLink.query.filter_by(discipline_id=discipline.id).count()
        if plans_count > 0:
            flash(
                f'Невозможно удалить дисциплину "{discipline.name}", так как она используется в {plans_count} учебных планах.',
                'error')
            return redirect(url_for('main.admin_view_table', table_name='discipline'))

        # Проверяем наличие в нагрузке преподавателей
        assignments_count = TeacherAssignment.query.filter_by(discipline_id=discipline.id).count()
        if assignments_count > 0:
            flash(
                f'Невозможно удалить дисциплину "{discipline.name}", так как она есть в нагрузке {assignments_count} преподавателей.',
                'error')
            return redirect(url_for('main.admin_view_table', table_name='discipline'))

        # Если все проверки пройдены - удаляем
        db.session.delete(discipline)
        db.session.commit()

        log_action(
            admin_id=current_user.id,
            operation_type='DELETE',
            table_name='discipline',
            record_id=discipline_id,
            old_data={'name': discipline.name}
        )

        flash(f'Дисциплина "{discipline.name}" успешно удалена.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении дисциплины: {str(e)}', 'error')

    return redirect(url_for('main.admin_view_table', table_name='discipline'))


def delete_study_group(group, group_id):
    """Специальная обработка удаления учебной группы"""
    try:
        # 1. Получаем информацию о группе для логирования
        group_number = group.number
        student_count = Student.query.filter_by(group_id=group.id).count()

        # 2. Проверяем, есть ли активные студенты (со статусом "учится")
        active_students = Student.query.filter_by(group_id=group.id, status='учится').count()
        if active_students > 0:
            flash(
                f'Невозможно удалить группу "{group_number}", так как в ней есть {active_students} активных студентов. Сначала переведите или отчислите студентов.',
                'error')
            return redirect(url_for('main.admin_view_table', table_name='study_group'))

        # 3. Сохраняем данные для логирования
        old_data = {
            'number': group.number,
            'plan_id': group.plan_id,
            'form_of_study': group.form_of_study,
            'current_year': group.current_year,
            'current_semester': group.current_semester,
            'students_count': student_count
        }

        # 4. Удаляем группу (каскадно удалятся студенты и нагрузка)
        db.session.delete(group)
        db.session.commit()

        # 5. Логируем действие
        log_action(
            admin_id=current_user.id,
            operation_type='DELETE',
            table_name='study_group',
            record_id=group_id,
            old_data=old_data
        )

        flash(f'Группа "{group_number}" успешно удалена. Удалено студентов: {student_count}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении группы: {str(e)}', 'error')

    return redirect(url_for('main.admin_view_table', table_name='study_group'))


def delete_study_plan(plan, plan_id):
    """Специальная обработка удаления учебного плана"""
    try:
        # 1. Проверяем, есть ли группы, обучающиеся по этому плану
        groups_count = StudyGroup.query.filter_by(plan_id=plan.id).count()
        if groups_count > 0:
            flash(
                f'Невозможно удалить учебный план (год {plan.approval_year}), так как по нему обучается {groups_count} групп. Сначала удалите группы или переназначьте их на другой план.',
                'error')
            return redirect(url_for('main.admin_view_table', table_name='study_plan'))

        # 2. Проверяем, есть ли связи с дисциплинами
        links_count = PlanDisciplineLink.query.filter_by(plan_id=plan.id).count()
        if links_count > 0:
            flash(
                f'Невозможно удалить учебный план (год {plan.approval_year}), так как он содержит {links_count} дисциплин. Сначала удалите связи с дисциплинами.',
                'error')
            return redirect(url_for('main.admin_view_table', table_name='study_plan'))

        # 3. Сохраняем данные для логирования
        old_data = {
            'approval_year': plan.approval_year,
            'direction_id': plan.direction_id,
            'duration_semesters': plan.duration_semesters,
            'groups_count': groups_count,
            'links_count': links_count
        }

        # 4. Удаляем план
        db.session.delete(plan)
        db.session.commit()

        # 5. Логируем действие
        log_action(
            admin_id=current_user.id,
            operation_type='DELETE',
            table_name='study_plan',
            record_id=plan_id,
            old_data=old_data
        )

        flash(f'Учебный план (год {plan.approval_year}) успешно удален.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении учебного плана: {str(e)}', 'error')

    return redirect(url_for('main.admin_view_table', table_name='study_plan'))


def delete_study_direction(direction, direction_id):
    """Специальная обработка удаления направления подготовки"""
    try:
        # 1. Проверяем, есть ли учебные планы у этого направления
        plans_count = StudyPlan.query.filter_by(direction_id=direction.id).count()
        if plans_count > 0:
            flash(
                f'Невозможно удалить направление "{direction.name}" (код {direction.code}), так как у него есть {plans_count} учебных планов. Сначала удалите все учебные планы.',
                'error')
            return redirect(url_for('main.admin_view_table', table_name='study_direction'))

        # 2. Сохраняем данные для логирования
        old_data = {
            'code': direction.code,
            'name': direction.name,
            'level': direction.level,
            'profile': direction.profile,
            'plans_count': plans_count
        }

        # 3. Удаляем направление
        db.session.delete(direction)
        db.session.commit()

        # 4. Логируем действие
        log_action(
            admin_id=current_user.id,
            operation_type='DELETE',
            table_name='study_direction',
            record_id=direction_id,
            old_data=old_data
        )

        flash(f'Направление "{direction.name}" (код {direction.code}) успешно удалено.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении направления: {str(e)}', 'error')

    return redirect(url_for('main.admin_view_table', table_name='study_direction'))


def delete_position(position, position_id):
    """Специальная обработка удаления должности"""
    try:
        # 1. Проверяем права на удаление через существующую функцию
        if not check_position_delete_permission(position_id):
            # Функция уже содержит flash сообщения, но добавим дополнительные проверки
            if position.rank == 5:
                flash('Нельзя удалить должность с максимальным рангом (ранг 5).', 'error')
            else:
                admin_count = Admin.query.filter_by(position_id=position.id).count()
                if admin_count > 0:
                    flash(
                        f'Нельзя удалить должность "{position.title}", так как с ней связано {admin_count} администраторов. Сначала переназначьте или удалите администраторов.',
                        'error')
                else:
                    flash('У вас нет прав на удаление этой должности.', 'error')
            return redirect(url_for('main.admin_view_table', table_name='position'))

        # 2. Сохраняем данные для логирования
        old_data = {
            'title': position.title,
            'rank': position.rank,
            'permissions_mask': position.permissions_mask
        }

        # 3. Удаляем должность
        db.session.delete(position)
        db.session.commit()

        # 4. Логируем действие
        log_action(
            admin_id=current_user.id,
            operation_type='DELETE',
            table_name='position',
            record_id=position_id,
            old_data=old_data
        )

        flash(f'Должность "{position.title}" успешно удалена.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении должности: {str(e)}', 'error')

    return redirect(url_for('main.admin_view_table', table_name='position'))


def delete_contact(contact, contact_id):
    """Специальная обработка удаления контакта"""
    try:
        # 1. Проверяем, используется ли контакт
        student = Student.query.filter_by(contact_id=contact.id).first()
        teacher = Teacher.query.filter_by(contact_id=contact.id).first()
        admin = Admin.query.filter_by(contact_id=contact.id).first()

        if student or teacher or admin:
            used_by = []
            if student:
                used_by.append(f'студентом {student.surname} {student.name}')
            if teacher:
                used_by.append(f'преподавателем {teacher.surname} {teacher.name}')
            if admin:
                used_by.append(f'администратором {admin.surname} {admin.name}')

            flash(f'Невозможно удалить контакт, так как он используется: {", ".join(used_by)}.', 'error')
            return redirect(url_for('main.admin_view_table', table_name='contact'))

        # 2. Сохраняем данные для логирования
        old_data = {
            'phone': contact.phone,
            'email': contact.email,
            'snils': contact.snils,
            'passport_series': contact.passport_series,
            'passport_number': contact.passport_number
        }

        # 3. Удаляем контакт
        db.session.delete(contact)
        db.session.commit()

        # 4. Логируем действие
        log_action(
            admin_id=current_user.id,
            operation_type='DELETE',
            table_name='contact',
            record_id=contact_id,
            old_data=old_data
        )

        flash('Контакт успешно удален.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении контакта: {str(e)}', 'error')

    return redirect(url_for('main.admin_view_table', table_name='contact'))


def delete_admin_user(admin, admin_id):
    """Специальная обработка удаления администратора"""
    try:
        # 1. Проверяем, не является ли администратор единственным с рангом 5
        if admin.position.rank == 5:
            # Проверяем, есть ли другие администраторы с рангом 5
            other_admins = Admin.query.filter(
                Admin.position_id == admin.position_id,
                Admin.id != admin.id
            ).count()
            if other_admins == 0:
                flash('Нельзя удалить единственного администратора с максимальным рангом (ранг 5).', 'error')
                return redirect(url_for('main.admin_view_table', table_name='admin_user'))

        # 2. Сохраняем ID контакта и информацию для логирования
        contact_id = admin.contact_id
        admin_info = {
            'surname': admin.surname,
            'name': admin.name,
            'patronymic': admin.patronymic,
            'login': admin.login,
            'work_email': admin.work_email,
            'position_id': admin.position_id
        }

        # 3. Проверяем, есть ли записи в журнале аудита
        actions_count = ActionLog.query.filter_by(admin_id=admin.id).count()

        # 4. Удаляем администратора (но НЕ удаляем записи в журнале)
        # Для этого сначала обновляем записи в ActionLog, устанавливая admin_id = NULL
        if actions_count > 0:
            # Обновляем записи в журнале, чтобы они не ссылались на удаленного администратора
            ActionLog.query.filter_by(admin_id=admin.id).update(
                {ActionLog.admin_id: None}
            )
            db.session.commit()

        # 5. Удаляем администратора
        db.session.delete(admin)
        db.session.commit()

        # 6. Удаляем контакт, если он был
        if contact_id:
            contact = Contact.query.get(contact_id)
            if contact:
                db.session.delete(contact)
                db.session.commit()

        # 7. Логируем действие
        log_action(
            admin_id=current_user.id,  # Текущий администратор
            operation_type='DELETE',
            table_name='admin_user',
            record_id=admin_id,
            old_data=admin_info
        )

        flash(f'Администратор "{admin.surname} {admin.name}" успешно удален. Записи в журнале аудита сохранены.',
              'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении администратора: {str(e)}', 'error')

    return redirect(url_for('main.admin_view_table', table_name='admin_user'))


@main_bp.route('/admin/check_dependencies/<table_name>/<int:record_id>')
@login_required
def admin_check_dependencies(table_name, record_id):
    """Проверяет наличие зависимостей для записи"""
    if current_user.__class__.__name__ != 'Admin':
        return jsonify({'error': 'Доступ запрещен'}), 403

    dependencies = check_dependencies(table_name, record_id)
    return jsonify({'dependencies': dependencies})


def check_dependencies(table_name, record_id):
    """Проверяет наличие связанных записей в других таблицах и возвращает список понятных названий"""
    dependencies = []

    # Словарь зависимостей для каждой таблицы
    dependency_map = {
        'student': [],
        'teacher': [
            ('TeacherAssignment', TeacherAssignment, 'teacher_id')
        ],
        'discipline': [
            ('AssessmentEvent', AssessmentEvent, 'discipline_id'),
            ('PlanDisciplineLink', PlanDisciplineLink, 'discipline_id'),
            ('TeacherAssignment', TeacherAssignment, 'discipline_id')
        ],
        'study_group': [],
        'study_plan': [],
        'study_direction': [],
        'position': [],
        'contact': [],
        'teacher_assignment': [],
        'plan_discipline_link': [],
        'assessment_event': [],
        'admin_user': []
    }

    table_names_ru = {
        'AssessmentEvent': 'Зачётные мероприятия',
        'Student': 'Студенты',
        'Teacher': 'Преподаватели',
        'Admin': 'Администраторы',
        'StudyGroup': 'Учебные группы',
        'StudyPlan': 'Учебные планы',
        'StudyDirection': 'Направления',
        'Position': 'Должности',
        'Contact': 'Контакты',
        'TeacherAssignment': 'Нагрузка преподавателей',
        'PlanDisciplineLink': 'Связь план-дисциплина',
        'ActionLog': 'Журнал действий'
    }

    deps = dependency_map.get(table_name, [])
    for dep_table_name, dep_model, dep_field in deps:
        count = dep_model.query.filter(getattr(dep_model, dep_field) == record_id).count()
        if count > 0:
            ru_name = table_names_ru.get(dep_table_name, dep_table_name)
            # Получаем более детальную информацию
            if count == 1:
                dependencies.append(f'{ru_name} (1 запись)')
            else:
                dependencies.append(f'{ru_name} ({count} записей)')

    return dependencies

def get_dependency_warning(table_name, record_id):
    """Возвращает предупреждение о связанных записях"""
    deps = check_dependencies(table_name, record_id)
    if deps:
        dep_list = ', '.join(deps)
        return f'Внимание! Удаление этой записи также удалит связанные данные: {dep_list}. Продолжить?'
    return None


@main_bp.route('/admin/get_record/<table_name>/<int:record_id>')
@login_required
def admin_get_record(table_name, record_id):
    """Возвращает данные записи в формате JSON для модального окна редактирования"""
    if current_user.__class__.__name__ != 'Admin':
        return jsonify({'error': 'Доступ запрещен'}), 403

    # Проверяем право на редактирование
    if table_name == 'position':
        if not check_position_edit_permission(record_id):
            return jsonify({'error': 'Нельзя редактировать должность с максимальным рангом'}), 403
    else:
        if not check_edit_permission(table_name):
            return jsonify({'error': f'У вас нет прав на редактирование таблицы "{table_name}"'}), 403

    model = MODELS_MAP.get(table_name)
    if not model:
        return jsonify({'error': 'Таблица не найдена'}), 404

    record = model.query.get(record_id)
    if not record:
        return jsonify({'error': 'Запись не найдена'}), 404

    columns = [col.name for col in model.__table__.columns if 'password' not in col.name]
    data = {}
    for col in columns:
        value = getattr(record, col, None)
        if value is not None:
            if isinstance(value, (datetime, date)):
                value = value.isoformat()
            elif isinstance(value, (db.Model,)):
                value = value.id if hasattr(value, 'id') else str(value)
        data[col] = value

    # Для таблицы position добавляем информацию о правах (без is_max_rank, так как проверяем по rank)
    if table_name == 'position':
        data['permissions_list'] = record.get_permissions_list()
    return jsonify(data)


@main_bp.route('/admin/update/<table_name>/<int:record_id>', methods=['POST'])
@login_required
def admin_update_record(table_name, record_id):
    """Обновляет запись в указанной таблице"""
    if current_user.__class__.__name__ != 'Admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('main.admin_dashboard'))

    # Проверяем право на редактирование
    if table_name == 'position':
        if not check_position_edit_permission(record_id):
            flash('Нельзя редактировать должность с максимальным рангом.', 'error')
            return redirect(url_for('main.admin_view_table', table_name=table_name))
    else:
        if not check_edit_permission(table_name):
            flash(f'У вас нет прав на редактирование таблицы "{table_name}".', 'error')
            return redirect(url_for('main.admin_view_table', table_name=table_name))

    model = MODELS_MAP.get(table_name)
    if not model:
        abort(404)

    record = model.query.get(record_id)
    if not record:
        flash('Запись не найдена.', 'error')
        return redirect(url_for('main.admin_view_table', table_name=table_name))

    columns = [col.name for col in model.__table__.columns if 'password' not in col.name]
    old_data = get_record_data(record, columns)

    try:
        for col in columns:
            if col == 'id':
                continue

            # Для таблицы position блокируем изменение rank и permissions_mask у максимальной должности
            if table_name == 'position':
                # Если это максимальная должность, пропускаем поля rank и permissions_mask
                if record.rank == 5 and col in ['rank', 'permissions_mask']:
                    continue

                # Если пытаемся установить ранг 5
                if col == 'rank':
                    value = request.form.get(col)
                    if value and int(value) == 5:
                        flash('Нельзя установить ранг 5 (максимальный ранг).', 'error')
                        return redirect(url_for('main.admin_view_table', table_name=table_name))

            value = request.form.get(col)
            if value is not None and value != '':
                column = getattr(model, col)
                if isinstance(column.type, db.Integer):
                    setattr(record, col, int(value))
                elif isinstance(column.type, db.Date):
                    setattr(record, col, datetime.strptime(value, '%Y-%m-%d').date())
                elif isinstance(column.type, db.DateTime):
                    setattr(record, col, datetime.strptime(value, '%Y-%m-%dT%H:%M'))
                else:
                    setattr(record, col, value)

        db.session.commit()

        new_data = get_record_data(record, columns)

        log_action(
            admin_id=current_user.id,
            operation_type='UPDATE',
            table_name=table_name,
            record_id=record_id,
            old_data=old_data,
            new_data=new_data
        )

        flash('Запись успешно обновлена.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении: {str(e)}', 'error')

    return redirect(url_for('main.admin_view_table', table_name=table_name))


@main_bp.route('/admin/create/<table_name>', methods=['POST'])
@login_required
def admin_create_record(table_name):
    """Создает новую запись в указанной таблице"""
    if current_user.__class__.__name__ != 'Admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('main.admin_dashboard'))

    # Проверяем право на редактирование
    if table_name == 'position':
        if not check_position_edit_permission():
            flash('У вас нет прав на создание должностей.', 'error')
            return redirect(url_for('main.admin_view_table', table_name=table_name))
    else:
        if not check_edit_permission(table_name):
            flash(f'У вас нет прав на создание записей в таблице "{table_name}".', 'error')
            return redirect(url_for('main.admin_view_table', table_name=table_name))

    model = MODELS_MAP.get(table_name)
    if not model:
        abort(404)

    try:
        # Создаем новый экземпляр модели
        new_record = model()

        # Заполняем поля из формы
        columns = [col.name for col in model.__table__.columns if 'password' not in col.name and col.name != 'id']

        for col in columns:
            value = request.form.get(col)
            if value is not None and value != '':
                column = getattr(model, col)
                if isinstance(column.type, db.Integer):
                    # Для таблицы position проверяем, что ранг не 5
                    if table_name == 'position' and col == 'rank':
                        if int(value) == 5:
                            flash('Нельзя создать должность с рангом 5 (максимальный ранг).', 'error')
                            return redirect(url_for('main.admin_view_table', table_name=table_name))
                    setattr(new_record, col, int(value))
                elif isinstance(column.type, db.Date):
                    setattr(new_record, col, datetime.strptime(value, '%Y-%m-%d').date())
                elif isinstance(column.type, db.DateTime):
                    setattr(new_record, col, datetime.strptime(value, '%Y-%m-%dT%H:%M'))
                else:
                    setattr(new_record, col, value)

        db.session.add(new_record)
        db.session.commit()

        # Логируем создание
        new_data = get_record_data(new_record,
                                   [col.name for col in model.__table__.columns if 'password' not in col.name])
        log_action(
            admin_id=current_user.id,
            operation_type='INSERT',
            table_name=table_name,
            record_id=new_record.id,
            new_data=new_data
        )

        flash('Запись успешно создана.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при создании: {str(e)}', 'error')

    return redirect(url_for('main.admin_view_table', table_name=table_name))


@main_bp.route('/admin/get_table_structure/<table_name>')
@login_required
def admin_get_table_structure(table_name):
    """Возвращает структуру таблицы для создания новой записи"""
    if current_user.__class__.__name__ != 'Admin':
        return jsonify({'error': 'Доступ запрещен'}), 403

    model = MODELS_MAP.get(table_name)
    if not model:
        return jsonify({'error': 'Таблица не найдена'}), 404

    columns = {}
    for col in model.__table__.columns:
        if 'password' in col.name:
            continue
        columns[col.name] = {
            'type': str(col.type),
            'nullable': col.nullable
        }

    return jsonify(columns)


def increment_group_number(number):
    """Увеличивает номер группы на один курс"""
    # Пример: 0291-04 -> 0292-04
    # Пример: 0292-01M -> 0293-01M
    # Пример: 0424-01 -> 0425-01 (переход от 4 к 5 курсу, как на скриншоте)

    # Проверяем, есть ли буква M в конце (магистратура)
    is_magistr = number.endswith('M')
    if is_magistr:
        number = number[:-1]  # Убираем M

    # Разбираем номер: XXYY-ZZ
    parts = number.split('-')
    if len(parts) != 2:
        return number  # Неожиданный формат, возвращаем как есть

    prefix = parts[0]  # Например, 0291
    suffix = parts[1]  # Например, 04

    # Увеличиваем курс (последние две цифры префикса)
    # 91 -> 92, 92 -> 93, 93 -> 94, 94 -> 95, 24 -> 25 (для 4 курса)
    course_code = prefix[-2:]  # Последние 2 цифры
    rest = prefix[:-2]  # Остальная часть

    try:
        course_num = int(course_code)
        # Логика перехода: 91->92, 92->93, 93->94, 94->95, 24->25 (4 курс)
        if course_num == 91:
            new_course = 92
        elif course_num == 92:
            new_course = 93
        elif course_num == 93:
            new_course = 94
        elif course_num == 94:
            new_course = 95
        elif course_num == 95:
            new_course = 95  # 5 курс - последний, не меняем
        elif course_num == 24:
            new_course = 25  # 4 курс (0424) -> 5 курс (0425)
        elif course_num == 25:
            new_course = 25  # 5 курс - последний
        else:
            # Если не знаем, просто увеличиваем на 1
            new_course = course_num + 1
            if new_course > 99:
                new_course = 99

        new_course_str = str(new_course).zfill(2)
        new_prefix = rest + new_course_str
        new_number = f"{new_prefix}-{suffix}"

        if is_magistr:
            new_number += 'M'

        return new_number
    except ValueError:
        # Если не удалось распарсить, возвращаем как есть
        return number


def log_semester_transition(changes):
    """Специальное логирование перехода на новый семестр"""
    # Создаем запись в ActionLog с особым форматом
    log_entry = {
        'type': 'SEMESTER_TRANSITION',
        'timestamp': datetime.utcnow().isoformat(),
        'changes': changes,
        'admin_id': current_user.id,
        'admin_name': f"{current_user.surname} {current_user.name}"
    }

    # Сохраняем как обычную запись, но с особым table_name
    action = ActionLog(
        admin_id=current_user.id,
        operation_type='SEMESTER_TRANSITION',
        table_name='system',
        record_id=0,
        old_data=json.dumps(0),
        new_data=json.dumps(0)
    )
    db.session.add(action)
    db.session.commit()


@main_bp.route('/admin/advance_semester', methods=['POST'])
@login_required
def advance_semester():
    """Перевод всех групп на следующий семестр (только для rank=5)"""
    if current_user.__class__.__name__ != 'Admin':
        flash('Доступ запрещен.', 'error')
        return redirect(url_for('main.admin_dashboard'))

    if current_user.position.rank != 5:
        flash('Только системный администратор может выполнять переход на новый семестр.', 'error')
        return redirect(url_for('main.admin_dashboard'))

    try:
        # Получаем все группы
        groups = StudyGroup.query.all()

        # Логируем изменения
        changes = []

        for group in groups:
            old_number = group.number
            old_year = group.current_year
            old_semester = group.current_semester

            # 1. Обновляем номер группы (увеличиваем цифру курса на 1)
            # Формат: XXYY-ZZ, где YY - код курса (91, 92, 93, 94, 95)
            # Для магистров: XXYY-ZZM
            new_number = increment_group_number(group.number)

            # 2. Увеличиваем курс и семестр
            group.current_year += 1
            group.current_semester += 1
            group.number = new_number

            changes.append({
                'group_id': group.id,
                'old_number': old_number,
                'new_number': new_number,
                'old_year': old_year,
                'new_year': group.current_year,
                'old_semester': old_semester,
                'new_semester': group.current_semester,
                'student_count': len(group.students)
            })

        db.session.commit()

        # Логируем переход
        log_semester_transition(changes)

        flash(f'Переход на новый семестр выполнен успешно. Обновлено групп: {len(groups)}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при переходе на новый семестр: {str(e)}', 'error')

    return redirect(url_for('main.admin_dashboard'))


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