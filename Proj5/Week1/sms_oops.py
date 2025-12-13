# =========================
# Entity / Model
# =========================
class Student:
    def __init__(self, student_id: int, name: str, marks: float):
        self.id = student_id
        self.name = name
        self.marks = marks


# =========================
# Data Layer (Repository)
# =========================
class StudentRepository:
    def __init__(self):
        self._students = {}
        self._next_id = 1

    def generate_id(self):
        student_id = self._next_id
        self._next_id += 1
        return student_id

    def add(self, student: Student):
        self._students[student.id] = student

    def get(self, student_id: int):
        return self._students.get(student_id)

    def delete(self, student_id: int):
        return self._students.pop(student_id, None)

    def list_all(self):
        return list(self._students.values())


# =========================
# Business Logic Layer
# =========================
class StudentService:
    def __init__(self, repository: StudentRepository):
        self.repository = repository

    def create_student(self, name: str, marks: float):
        if not name.strip():
            raise ValueError("Name cannot be empty")

        if marks < 0 or marks > 100:
            raise ValueError("Marks must be between 0 and 100")

        student_id = self.repository.generate_id()
        student = Student(student_id, name, marks)
        self.repository.add(student)
        return student

    def update_marks(self, student_id: int, marks: float):
        if marks < 0 or marks > 100:
            raise ValueError("Marks must be between 0 and 100")

        student = self.repository.get(student_id)
        if not student:
            raise ValueError("Student not found")

        student.marks = marks
        return student

    def delete_student(self, student_id: int):
        student = self.repository.delete(student_id)
        if not student:
            raise ValueError("Student not found")
        return student

    def list_students(self):
        return self.repository.list_all()


# =========================
# Presentation Layer (CLI)
# =========================
def main():
    repository = StudentRepository()
    service = StudentService(repository)

    print("Welcome to Student Manager")

    while True:
        print("\nOptions:")
        print("1. Add student")
        print("2. View students")
        print("3. Update marks")
        print("4. Delete student")
        print("5. Exit")

        choice = input("Choose an option: ")

        try:
            if choice == "1":
                name = input("Enter name: ")
                marks = float(input("Enter marks: "))
                student = service.create_student(name, marks)
                print(f"Student added with ID {student.id}")

            elif choice == "2":
                students = service.list_students()
                if not students:
                    print("No students found")
                else:
                    for s in students:
                        print(f"ID: {s.id}, Name: {s.name}, Marks: {s.marks}")

            elif choice == "3":
                student_id = int(input("Enter student ID: "))
                marks = float(input("Enter new marks: "))
                service.update_marks(student_id, marks)
                print("Marks updated successfully")

            elif choice == "4":
                student_id = int(input("Enter student ID: "))
                service.delete_student(student_id)
                print("Student deleted")

            elif choice == "5":
                print("Goodbye!")
                break

            else:
                print("Invalid choice")

        except ValueError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
