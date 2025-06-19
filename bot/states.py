from aiogram.fsm.state import StatesGroup, State

class Form(StatesGroup):
    task_title = State()
    task_description = State()
    task_due_date = State()
    task_due_time = State()
    task_category = State()  # новый шаг для выбора категории
    category_name = State()
    category_rename = State()
    task_category_filter = State()
