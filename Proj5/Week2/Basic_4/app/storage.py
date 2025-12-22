from models import Notes,Notes_ID
from typing import Dict
from datetime import datetime
import json


_notes_dict: Dict[int,Notes_ID] ={}
_current_id: int= 0


def create_notes(notes:Notes) -> Notes_ID:
    global _current_id
    _current_id += 1
    
    note=Notes_ID(
        id= _current_id,
        title= notes.title,
        content=notes.content,
        created_at=datetime.utcnow().isoformat(),
        is_archived=True
    )
    
    _notes_dict[note.id] = note
    return note


def get_all():
    return list(_notes_dict.values())


def get_by_id(id: int) -> Notes_ID | None:
    return _notes_dict.get(id)
    
def update_notes(note_id: int, note_data: Notes) -> Notes_ID | None:
    if note_id not in _notes_dict:
        return None

    updated_item = Notes_ID(id=note_id, **note_data.dict())
    _notes_dict[note_id] = updated_item
    return updated_item