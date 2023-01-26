from datetime import date, timedelta


def get_schedule(schedule_item) -> [[str, str]]:
    turn_offs = schedule_item["turn_offs"]["L"]

    schedule = []

    for turn_off in turn_offs:
        start = turn_off["M"]["start"]["S"]
        end = turn_off["M"]["end"]["S"]

        schedule.append([start, end])

    return schedule


def get_schedule_message(schedule, date_start):
    message = "Графік вимкнення: "

    item_messages = []
    for item in schedule:
        item_messages.append(f"{item[0]}-{item[1]}")

    if str(date.today()) == date_start:
        date_message = "Діє відсьогодні."
    elif str(date.today() + timedelta(days=1)) == date_start:
        date_message = "Діє відзавтра."
    else:
        date_message = ""

    return message + ", ".join(item_messages) + ". " + date_message
