students = {}
next_id = 1


def add_student(name, marks):
    global next_id

    if not name:
        return "Name cannot be empty"

    if marks < 0 or marks > 100:
        return "Marks must be between 0 and 100"

    students[next_id] = {
        "name": name,
        "marks": marks
    }

    msg = f"Student added with ID {next_id}"
    next_id += 1
    return msg


def show_students():
    if not students:
        return "No students found"

    result = []
    for sid, data in students.items():
        result.append(
            f"ID: {sid}, Name: {data['name']}, Marks: {data['marks']}"
        )
    return "\n".join(result)


def update_marks(student_id, marks):
    if student_id not in students:
        return "Student ID not found"

    if marks < 0 or marks > 100:
        return "Marks must be between 0 and 100"

    students[student_id]["marks"] = marks
    return "Marks updated successfully"


def delete_student(student_id):
    if student_id not in students:
        return "Student ID not found"

    del students[student_id]
    return "Student deleted"


print("Welcome to Student Manager")

while True:
    print("\nOptions: add | show | update | delete | exit")
    choice = input("Enter command: ").lower()

    if choice == "add":
        name = input("Enter name: ")
        try:
            marks = float(input("Enter marks: "))
            print(add_student(name, marks))
        except ValueError:
            print("Invalid marks")

    elif choice == "show":
        print(show_students())

    elif choice == "update":
        try:
            sid = int(input("Enter student ID: "))
            marks = float(input("Enter new marks: "))
            print(update_marks(sid, marks))
        except ValueError:
            print("Invalid input")

    elif choice == "delete":
        try:
            sid = int(input("Enter student ID: "))
            print(delete_student(sid))
        except ValueError:
            print("Invalid ID")

    elif choice == "exit":
        print("Goodbye")
        break

    else:
        print("Invalid command")
