d={}

def add(name,marks):
    length = len(d.keys())+1
    d[len(d.keys())+1] = {"name":name,"marks":marks}
    return f"{name} whose score is {marks} is added and the id is {length}"

def show():
    return d

def update_marks(ids,marks):
    if ids in d.keys():
        names= d[ids][0]
        d[ids][1] = marks
        return f"Marks of the student{names} has been updated and now it is {marks}"
        

def delete(ids):
    if ids in d.keys():
        d.pop(ids)
        return 'Deleted'
    return "Key not in Dict"
    
def exit():
    quit()
    
    


print("welcome")


while True:
    x=input("please enter a function: ")

    if x== 'add':
        name= input("Enter the name: ")
        marks= float(input("Enter the marks: "))
        print(add(name,marks))


    if x== 'show':
        print(show())


    if x== 'update_marks':
        ids = int('Enter the Id')
        marks= float("Enter the marks")
        print(update_marks(ids,marks))


    if x== 'delete':
        ids = int(input("Enter the id: "))
        delete(ids)

    if x== 'exit':
        exit()