import random


subjects = ["Celeb 1","Celeb 2","Celeb 3"]

actions = ["launces","cancels","dances with","sleeps with","Declares war on","Celebrates"]

places_or_things = ["At place 1","at place 2","At place 3","at place 4"]

while True:    
    further_action = input("Do you want headline? Yes/No: ").strip()
    if further_action.lower() == 'yes':
        subject = random.choice(subjects)
        action = random.choice(actions)
        place = random.choice(places_or_things)
        headline = f"Our {subject} {action} {place}."
        print(headline)
    else:
        quit()

# Can be imporvised more