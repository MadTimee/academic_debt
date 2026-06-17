from app import create_app, db
from app.models import (
    Position, StudyDirection, StudyPlan, StudyGroup, Discipline,
    PlanDisciplineLink, Contact, Admin, Teacher, Student, AssessmentEvent, TeacherAssignment
)
from werkzeug.security import generate_password_hash
from datetime import date


def seed_database():
    app = create_app()

    with app.app_context():
        db.drop_all()
        db.create_all()
        print("База данных очищена и пересоздана.")

        # 1. Должности с битовыми масками прав
        # Системный администратор (rank=5) - имеет доступ ко всему, включая права должностей
        pos_sysadmin = Position(
            title="Системный администратор",
            rank=5,
            permissions_mask=4095,  # Все 12 бит = 1 (все права)
            permissions_desc="Полный доступ ко всем таблицам, включая управление правами"
        )

        # Методист деканата (rank=2) - имеет доступ к студентам, группам, мероприятиям, но не к администраторам и должностям
        pos_methodist = Position(
            title="Методист деканата",
            rank=2,
            permissions_mask=(
                    1 |  # student
                    8 |  # study_group
                    256 |  # contact
                    512  # assessment_event
            ),
            permissions_desc="Редактирование студентов, групп, контактов и зачётных мероприятий"
        )

        # Старший методист (rank=3) - больше прав, но не может управлять администраторами и должностями
        pos_senior_methodist = Position(
            title="Старший методист",
            rank=3,
            permissions_mask=(
                    1 |  # student
                    2 |  # teacher
                    8 |  # study_group
                    16 |  # discipline
                    32 |  # study_plan
                    64 |  # study_direction
                    256 |  # contact
                    512 |  # assessment_event
                    1024 |  # teacher_assignment
                    2048  # plan_discipline_link
            ),
            permissions_desc="Редактирование всех учебных данных, кроме администраторов и должностей"
        )

        db.session.add_all([pos_sysadmin, pos_methodist, pos_senior_methodist])
        db.session.commit()

        # 2. Направление и план
        direction = StudyDirection(
            level="бакалавриат", code="02.03.01", name="Математика и компьютерные науки",
            profile="Прикладная математика"
        )
        db.session.add(direction)
        db.session.commit()

        study_plan = StudyPlan(direction_id=direction.id, approval_year=2024, duration_semesters=8)
        db.session.add(study_plan)
        db.session.commit()

        # 3. Группы
        group1 = StudyGroup(
            number="0292-04",
            plan_id=study_plan.id,
            form_of_study="очная",
            current_year=2,
            current_semester=3
        )
        group2 = StudyGroup(
            number="0291-03",
            plan_id=study_plan.id,
            form_of_study="очная",
            current_year=1,
            current_semester=1
        )
        db.session.add_all([group1, group2])
        db.session.commit()

        # 4. Дисциплины
        disc_math = Discipline(name="Высшая математика")
        disc_python = Discipline(name="Программирование на Python")
        disc_physics = Discipline(name="Физика")
        db.session.add_all([disc_math, disc_python, disc_physics])
        db.session.commit()

        # 5. Связь План-Дисциплина
        link_math_3 = PlanDisciplineLink(plan_id=study_plan.id, discipline_id=disc_math.id, semester=3, hours=144,
                                         assessment_form="экзамен")
        link_math_4 = PlanDisciplineLink(plan_id=study_plan.id, discipline_id=disc_math.id, semester=4, hours=144,
                                         assessment_form="экзамен")
        link_python = PlanDisciplineLink(plan_id=study_plan.id, discipline_id=disc_python.id, semester=3, hours=108,
                                         assessment_form="зачет с оценкой")
        link_physics = PlanDisciplineLink(plan_id=study_plan.id, discipline_id=disc_physics.id, semester=1, hours=108,
                                          assessment_form="экзамен")
        db.session.add_all([link_math_3, link_math_4, link_python, link_physics])
        db.session.commit()

        # 6. Пользователи
        # Системный администратор (самый высокий ранг)
        admin = Admin(
            surname="Админов",
            name="Админ",
            patronymic="Админович",
            position_id=pos_sysadmin.id,
            work_email="admin@pskovgu.ru",
            login="admin",
            password_hash=generate_password_hash("123"),
            reg_date=date.today()
        )

        # Методист (средний ранг)
        methodist = Admin(
            surname="Методистова",
            name="Анна",
            patronymic="Ивановна",
            position_id=pos_methodist.id,
            work_email="method@pskovgu.ru",
            login="methodist",
            password_hash=generate_password_hash("123"),
            reg_date=date.today()
        )

        # Старший методист (более высокий ранг)
        senior_methodist = Admin(
            surname="Старшова",
            name="Елена",
            patronymic="Петровна",
            position_id=pos_senior_methodist.id,
            work_email="senior@pskovgu.ru",
            login="senior",
            password_hash=generate_password_hash("123"),
            reg_date=date.today()
        )

        teacher = Teacher(
            surname="Преподаватель",
            name="Петр",
            patronymic="Сергеевич",
            work_email="teacher@pskovgu.ru",
            login="teacher",
            password_hash=generate_password_hash("123"),
            reg_date=date.today()
        )

        student1 = Student(
            surname="Иванов",
            name="Иван",
            patronymic="Иванович",
            student_id_number="111",
            group_id=group1.id,
            status="учится",
            login="ivanov",
            password_hash=generate_password_hash("123"),
            reg_date=date.today()
        )
        student2 = Student(
            surname="Петров",
            name="Петр",
            patronymic="Петрович",
            student_id_number="222",
            group_id=group1.id,
            status="учится",
            login="petrov",
            password_hash=generate_password_hash("123"),
            reg_date=date.today()
        )
        student3 = Student(
            surname="Сидоров",
            name="Сидор",
            patronymic="Сидорович",
            student_id_number="333",
            group_id=group2.id,
            status="учится",
            login="sidorov",
            password_hash=generate_password_hash("123"),
            reg_date=date.today()
        )

        db.session.add_all([admin, methodist, senior_methodist, teacher, student1, student2, student3])
        db.session.commit()

        # 6.1 Создание контактов для пользователей
        # Контакт для администратора
        contact_admin = Contact(
            passport_series="1111", passport_number="111111", passport_dept_code="111-111",
            passport_issue_date=date(2000, 1, 1), passport_issued_by="ОУФМС России по г. Псков",
            snils="111-111-111 11",
            region="Псковская область", district="", city="Псков", street="Ленина",
            building="1", block=None, apartment="1", postal_code="180000",
            phone="+7(8112)11-11-11", email="admin@pskovgu.ru"
        )

        # Контакт для методиста
        contact_methodist = Contact(
            passport_series="2222", passport_number="222222", passport_dept_code="222-222",
            passport_issue_date=date(2001, 2, 2), passport_issued_by="ОУФМС России по г. Псков",
            snils="222-222-222 22",
            region="Псковская область", district="", city="Псков", street="Кузнецкая",
            building="2", block=None, apartment="2", postal_code="180001",
            phone="+7(8112)22-22-22", email="method@pskovgu.ru"
        )

        # Контакт для старшего методиста
        contact_senior = Contact(
            passport_series="3333", passport_number="333333", passport_dept_code="333-333",
            passport_issue_date=date(2002, 3, 3), passport_issued_by="ОУФМС России по г. Псков",
            snils="333-333-333 33",
            region="Псковская область", district="", city="Псков", street="Народная",
            building="3", block=None, apartment="3", postal_code="180002",
            phone="+7(8112)33-33-33", email="senior@pskovgu.ru"
        )

        # Контакт для преподавателя
        contact_teacher = Contact(
            passport_series="4444", passport_number="444444", passport_dept_code="444-444",
            passport_issue_date=date(2003, 4, 4), passport_issued_by="ОУФМС России по г. Псков",
            snils="444-444-444 44",
            region="Псковская область", district="", city="Псков", street="Советская",
            building="4", block=None, apartment="4", postal_code="180003",
            phone="+7(8112)44-44-44", email="teacher@pskovgu.ru"
        )

        # Контакт для студента 1
        contact_student1 = Contact(
            passport_series="5555", passport_number="555555", passport_dept_code="555-555",
            passport_issue_date=date(2004, 5, 5), passport_issued_by="ОУФМС России по г. Псков",
            snils="555-555-555 55",
            region="Псковская область", district="", city="Псков", street="Первомайская",
            building="5", block=None, apartment="5", postal_code="180004",
            phone="+7(8112)55-55-55", email="ivanov@example.com"
        )

        # Контакт для студента 2
        contact_student2 = Contact(
            passport_series="6666", passport_number="666666", passport_dept_code="666-666",
            passport_issue_date=date(2005, 6, 6), passport_issued_by="ОУФМС России по г. Псков",
            snils="666-666-666 66",
            region="Псковская область", district="", city="Псков", street="Октябрьская",
            building="6", block=None, apartment="6", postal_code="180005",
            phone="+7(8112)66-66-66", email="petrov@example.com"
        )

        # Контакт для студента 3
        contact_student3 = Contact(
            passport_series="7777", passport_number="777777", passport_dept_code="777-777",
            passport_issue_date=date(2006, 7, 7), passport_issued_by="ОУФМС России по г. Псков",
            snils="777-777-777 77",
            region="Псковская область", district="", city="Псков", street="Мира",
            building="7", block=None, apartment="7", postal_code="180006",
            phone="+7(8112)77-77-77", email="sidorov@example.com"
        )

        # Добавляем все контакты в сессию
        db.session.add_all([
            contact_admin, contact_methodist, contact_senior,
            contact_teacher, contact_student1, contact_student2, contact_student3
        ])
        db.session.commit()

        # 6.2 Обновляем пользователей, привязывая контакты
        admin.contact_id = contact_admin.id
        methodist.contact_id = contact_methodist.id
        senior_methodist.contact_id = contact_senior.id
        teacher.contact_id = contact_teacher.id
        student1.contact_id = contact_student1.id
        student2.contact_id = contact_student2.id
        student3.contact_id = contact_student3.id

        # 7. Нагрузка преподавателя
        assign1 = TeacherAssignment(teacher_id=teacher.id, discipline_id=disc_math.id, group_id=group1.id, semester=3)
        assign2 = TeacherAssignment(teacher_id=teacher.id, discipline_id=disc_math.id, group_id=group1.id,
                                    semester=4)
        assign3 = TeacherAssignment(teacher_id=teacher.id, discipline_id=disc_physics.id, group_id=group2.id,
                                    semester=1)
        db.session.add_all([assign1, assign2, assign3])
        db.session.commit()

        # 8. Зачётные мероприятия
        event1 = AssessmentEvent(discipline_id=disc_math.id, student_id=student1.id, form="экзамен",
                                 attempt_type="основная", date=date(2024, 12, 20), grade="хорошо", semester=3,
                                 teacher_id=teacher.id)
        event2 = AssessmentEvent(discipline_id=disc_math.id, student_id=student2.id, form="экзамен",
                                 attempt_type="первая_пересдача", date=date(2025, 2, 10), grade="неудовлетворительно",
                                 semester=3, teacher_id=teacher.id)
        event3 = AssessmentEvent(discipline_id=disc_physics.id, student_id=student3.id, form="экзамен",
                                 attempt_type="основная", date=date(2024, 12, 25), grade="отлично", semester=1,
                                 teacher_id=teacher.id)

        event_gia = AssessmentEvent(
            discipline_id=disc_math.id,
            student_id=student1.id,
            form="ГИА",
            attempt_type="основная",
            date=date(2026, 6, 15),
            grade="хорошо",
            semester=8,
            teacher_id=teacher.id
        )
        db.session.add(event_gia)

        db.session.add_all([event1, event2, event3])
        db.session.commit()

        print("✅ База данных успешно наполнена!")
        print("🔑 Пароль для всех пользователей: 123")
        print("👤 Логины:")
        print("   - admin (Системный администратор) - полный доступ")
        print("   - methodist (Методист) - ограниченный доступ")
        print("   - senior (Старший методист) - расширенный доступ")
        print("   - teacher (Преподаватель)")
        print("   - ivanov, petrov, sidorov (Студенты)")
        print("\n📋 Права доступа:")
        print("   - Системный администратор: все таблицы (включая должности)")
        print("   - Старший методист: все таблицы, кроме администраторов и должностей")
        print("   - Методист: только студенты, группы, контакты, зачётные мероприятия")


if __name__ == '__main__':
    seed_database()