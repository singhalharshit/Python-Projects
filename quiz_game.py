print("Welcome to the Quiz Game!")

playing = input("Do you want to play? (yes/no): ")

if playing != "yes":
    quit()
print("Great! Let's start the game.")

answer= "What is the full form of CPU? "

if answer.lower() == "central processing unit":
    print("Correct answer")
else:
    print("wrong answer")