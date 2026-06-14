from app import create_app, db
from app.models import (
    Position, StudyDirection, StudyPlan, StudyGroup, Discipline,
    PlanDisciplineLink, Contact, Admin, Teacher, Student, AssessmentEvent
)
from werkzeug.security import generate_password_hash
from datetime import date, datetime


def seed_database():
    app = create_app()

    with app.app_context():
        # 1. Очищаем базу данных для чистого запуска (опционально, удобно для разработки)
        db.drop_all()
        db.create_all()
        print("База данных очищена и пересоздана.")

        # 2. Создаем должности
        pos_sysadmin = Position(title="Системный администратор", rank=5,
                                permissions_desc="Полный доступ, кроме удаления логов")
        pos_methodist = Position(title="Методист деканата", rank=2,
                                 permissions_desc="Редактирование оценок, статусов, групп")
        db.session.add_all([pos_sysadmin, pos_methodist])
        db.session.commit()

        # 3. Создаем направление подготовки
        direction = StudyDirection(
            level="бакалавриат",
            code="02.03.01",
            name="Математика и компьютерные науки",
            profile="Прикладная математика и информатика"
        )
        db.session.add(direction)
        db.session.commit()

        # 4. Создаем учебный план (2024 года)
        study_plan = StudyPlan(
            direction_id=direction.id,
            approval_year=2024,
            duration_semesters=8
        )
        db.session.add(study_plan)
        db.session.commit()

        # 5. Создаем учебную группу 0292-04
        study_group = StudyGroup(
            number="0292-04",
            plan_id=study_plan.id,
            form_of_study="очная",
            current_year=2
        )
        db.session.add(study_group)
        db.session.commit()

        # 6. Создаем дисциплины
        disc_math = Discipline(name="Высшая математика")
        disc_python = Discipline(name="Программирование на Python")
        db.session.add_all([disc_math, disc_python])
        db.session.commit()

        # 7. Связываем дисциплины с учебным планом
        link_math = PlanDisciplineLink(
            plan_id=study_plan.id,
            discipline_id=disc_math.id,
            semester=3,
            hours=144,
            assessment_form="экзамен"
        )
        link_python = PlanDisciplineLink(
            plan_id=study_plan.id,
            discipline_id=disc_python.id,
            semester=3,
            hours=108,
            assessment_form="зачет с оценкой"
        )
        db.session.add_all([link_math, link_python])
        db.session.commit()

        # 8. Создаем администраторов
        admin_sys = Admin(
            surname="Системный", name="Админ", patronymic="Админович",
            position_id=pos_sysadmin.id,
            work_email="sysadmin@pskovgu.ru",
            login="admin",
            password_hash=generate_password_hash("admin123"),
            reg_date=date.today()
        )
        admin_methodist = Admin(
            surname="Методистова", name="Анна", patronymic="Ивановна",
            position_id=pos_methodist.id,
            work_email="methodist@pskovgu.ru",
            login="methodist",
            password_hash=generate_password_hash("method123"),
            reg_date=date.today()
        )
        db.session.add_all([admin_sys, admin_methodist])
        db.session.commit()

        # 9. Создаем преподавателя
        teacher1 = Teacher(
            surname="Преподаватель", name="Петр", patronymic="Сергеевич",
            work_email="teacher@pskovgu.ru",
            login="teacher",
            password_hash=generate_password_hash("teacher123"),
            reg_date=date.today()
        )
        db.session.add(teacher1)
        db.session.commit()

        # 10. Создаем студентов группы 0292-04
        student1 = Student(
            surname="Иванов", name="Иван", patronymic="Иванович",
            student_id_number="12345678",
            group_id=study_group.id,
            status="учится",
            login="ivanov",
            password_hash=generate_password_hash("student123"),
            reg_date=date.today()
        )
        student2 = Student(
            surname="Петров", name="Петр", patronymic="Петрович",
            student_id_number="87654321",
            group_id=study_group.id,
            status="учится",
            login="petrov",
            password_hash=generate_password_hash("student123"),
            reg_date=date.today()
        )
        db.session.add_all([student1, student2])
        db.session.commit()

        # 11. Создаем зачётные мероприятия (оценки и попытки)
        # Студент 1: успешно сдал Высшую математику с основной попытки
        event1 = AssessmentEvent(
            discipline_id=disc_math.id,
            student_id=student1.id,
            form="экзамен",
            attempt_type="основная",
            date=date(2024, 12, 20),
            grade="хорошо",
            teacher_id=teacher1.id,
            semester=3
        )

        event2 = AssessmentEvent(
            discipline_id=disc_math.id,
            student_id=student2.id,
            form="экзамен",
            attempt_type="первая_пересдача",
            date=date(2025, 2, 10),
            grade="неудовлетворительно",
            teacher_id=teacher1.id,
            semester=3
        )

        event3 = AssessmentEvent(
            discipline_id=disc_python.id,
            student_id=student2.id,
            form="зачет с оценкой",
            attempt_type="основная",
            date=date(2024, 12, 22),
            grade="отлично",
            teacher_id=teacher1.id,
            semester=3
        )

        db.session.add_all([event1, event2, event3])
        db.session.commit()

        print("База данных успешно наполнена тестовыми данными!")
        print("Администратор: login='admin', password='admin123'")
        print("Методист: login='methodist', password='method123'")
        print("Преподаватель: login='teacher', password='teacher123'")
        print("Студент 1 (без долгов): login='ivanov', password='student123'")
        print("Студент 2 (с задолженностью по Высшей математике): login='petrov', password='student123'")


if __name__ == '__main__':
    seed_database()