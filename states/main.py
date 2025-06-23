from aiogram.fsm.state import StatesGroup, State

class MainStates(StatesGroup):
    idle                 = State()
    idle_account         = State()
    add_account          = State()

    idle_category        = State()
    add_category         = State()

    idle_tag             = State()
    add_tag              = State()

    idle_transaction     = State()
    add_transaction      = State()
    wait_report_month    = State()

    idle_budget          = State()
    add_budget           = State()

    idle_goal            = State()
    add_goal             = State()
    refill_goal          = State()

    idle_recurring       = State()
    add_recurring        = State()
