HISTORY_FILE = "history.txt"

def show_history():
    file = open(HISTORY_FILE,'r')
    lines = file.readlines()
    if len(lines) ==0:
        print("No Data Found")
    else:
        for i in reversed(lines):
            print(i.split())
    file.close()


def clear_history():
    file = open(HISTORY_FILE,'w')
    file.close()
    print('History Cleared')

def save_to_history(equation,result):
    file = open(HISTORY_FILE,'a')
    file.write(equation + "=" + str(result) + "\n")
    file.close


def calculate(user_input):
    split_input = user_input.split()
    if len(split_input)!=3:
        print("incorrect length")
        return
    
    num1= float(split_input[0])
    op=split_input[1]
    num2 = float(split_input[2])

    if op=='+':
        res = num1+num2
    elif op=='-':
        res = num1-num2
    elif op=='*':
        res = num1*num2
    elif op=='/':
        if num2 ==0:
            print("can't divide by 0")
            return
        res = num1/num2
    else:
        print("Invlaid Input") 

    if  int(res) == res:
        res = int(res)
    
    print("Result: ",res)

    save_to_history(user_input,res)


def main():
    print('----- Simple Calulator------')
    while True:
        user_input = input("Enter Calc (+-*/) or command (history,clear,exit): ")
        if user_input == 'exit':
            print('Goodbye')
            break
        elif user_input == 'history':
            show_history()
        elif user_input == 'clear':
            clear_history()
        else:
            calculate(user_input=user_input)

main()