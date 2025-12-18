from datetime import datetime


# =========================
# Entity / Model
# =========================

class Notes:
    def __init__(self,notes_id: int,title: str,content: str):
        self.id = notes_id
        self.title = title
        self.content = content
    

# =========================
# Data Layer (Repository)
# =========================

class NotesReposiotry:
    def __init__(self):
        self._notes = {}
        self._next_id = 1
        
    with open('notes.txt','w') as f:
        def generate_id(self,created_at):
            self._next_id = notes_id 
            self.created_at = created_at
            self._next_id +=1
            return notes_id

        def newNotes(self,notes:Notes):
            

        def get(self,id: int):
            return self._notes.get(notes_id)

        def get_all(self):
            return list(self._notes.values())

        def delete(self,notes_id:int):
            return self._notes.pop(notes_id,None)


# =========================
# Business Logic Layer
# =========================