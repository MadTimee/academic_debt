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

        # 1. Должности
        pos_sysadmin = Position(title="Системный администратор", rank=5, permissions_desc="Полный доступ")
        pos_methodist = Position(title="Методист деканата", rank=2, permissions_desc="Редактирование оценок и групп")
        db.session.add_all([pos_sysadmin, pos_methodist])
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

        # 3. Группы (РАЗНЫЙ текущий семестр для проверки логики)
        group1 = StudyGroup(number="0292-04", plan_id=study_plan.id, form_of_study="очная", current_year=2,
                            current_semester=3)
        group2 = StudyGroup(number="0292-05", plan_id=study_plan.id, form_of_study="очная", current_year=1,
                            current_semester=1)
        db.session.add_all([group1, group2])
        db.session.commit()

        # 4. Дисциплины
        disc_math = Discipline(name="Высшая математика")
        disc_python = Discipline(name="Программирование на Python")
        disc_physics = Discipline(name="Физика")
        db.session.add_all([disc_math, disc_python, disc_physics])
        db.session.commit()

        # 5. Связь План-Дисциплина (Вышмат идет и в 3, и в 4 семестре!)
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

        # 6. Пользователи (ВСЕ ПАРОЛИ: 123)
        admin = Admin(surname="Админов", name="Админ", patronymic="Админович", position_id=pos_sysadmin.id,
                      work_email="admin@pskovgu.ru", login="admin", password_hash=generate_password_hash("123"),
                      reg_date=date.today())
        methodist = Admin(surname="Методистова", name="Анна", patronymic="Ивановна", position_id=pos_methodist.id,
                          work_email="method@pskovgu.ru", login="methodist",
                          password_hash=generate_password_hash("123"), reg_date=date.today())
        teacher = Teacher(surname="Преподаватель", name="Петр", patronymic="Сергеевич", work_email="teacher@pskovgu.ru",
                          login="teacher", password_hash=generate_password_hash("123"), reg_date=date.today())

        student1 = Student(surname="Иванов", name="Иван", patronymic="Иванович", student_id_number="111",
                           group_id=group1.id, status="учится", login="ivanov",
                           password_hash=generate_password_hash("123"), reg_date=date.today())
        student2 = Student(surname="Петров", name="Петр", patronymic="Петрович", student_id_number="222",
                           group_id=group1.id, status="учится", login="petrov",
                           password_hash=generate_password_hash("123"), reg_date=date.today())
        student3 = Student(surname="Сидоров", name="Сидор", patronymic="Сидорович", student_id_number="333",
                           group_id=group2.id, status="учится", login="sidorov",
                           password_hash=generate_password_hash("123"), reg_date=date.today())

        db.session.add_all([admin, methodist, teacher, student1, student2, student3])
        db.session.commit()

        # 7. Нагрузка преподавателя (Включая нагрузку на 4 семестр для группы 0292-04, которая сейчас в 3-м!)
        assign1 = TeacherAssignment(teacher_id=teacher.id, discipline_id=disc_math.id, group_id=group1.id, semester=3)
        assign2 = TeacherAssignment(teacher_id=teacher.id, discipline_id=disc_math.id, group_id=group1.id,
                                    semester=4)  # Ловушка для проверки валидации
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

        db.session.add_all([event1, event2, event3])
        db.session.commit()

        print("✅ База данных успешно наполнена!")
        print("🔑 Пароль для всех пользователей: 123")
        print("👤 Логины: admin, methodist, teacher, ivanov, petrov, sidorov")


if __name__ == '__main__':
    seed_database()