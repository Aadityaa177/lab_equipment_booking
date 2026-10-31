
from datetime import time
from sqlalchemy import text
from app import app, db

DAYS = ["MON", "TUE", "WED", "THU", "FRI"]

MORNING = [
    ("08:00:00", "08:50:00"),
    ("08:51:00", "09:40:00"),
    ("09:51:00", "10:40:00"),
    ("10:41:00", "11:30:00"),
    ("11:40:00", "12:30:00"),
    ("12:31:00", "13:20:00"),
]

AFTERNOON = [
    ("14:00:00", "14:50:00"),
    ("14:51:00", "15:40:00"),
    ("15:51:00", "16:40:00"),
    ("16:41:00", "17:30:00"),
    ("17:40:00", "18:30:00"),
    ("18:31:00", "19:20:00"),
]

with app.app_context():
    with db.engine.begin() as conn:
        # Remove the temporary test slot.
        conn.execute(text("""
            DELETE FROM timetable_slots
            WHERE slot_code = 'TEST01'
        """))

        for day_index, day in enumerate(DAYS):
            periods = MORNING + AFTERNOON

            for period_index, (start, end) in enumerate(periods):
                if period_index < 6:
                    number = day_index * 6 + period_index + 1
                else:
                    number = 30 + day_index * 6 + period_index - 5

                slot_code = f"L{number}"

                conn.execute(text("""
                    INSERT INTO timetable_slots
                        (day_of_week, slot_code, start_time, end_time,
                         display_label)
                    VALUES
                        (:day, :code, :start, :end, :label)
                    ON DUPLICATE KEY UPDATE
                        start_time = VALUES(start_time),
                        end_time = VALUES(end_time),
                        display_label = VALUES(display_label)
                """), {
                    "day": day,
                    "code": slot_code,
                    "start": start,
                    "end": end,
                    "label": f"{start[:5]}–{end[:5]}"
                })

    print("Timetable seeded successfully: 60 slots, Monday to Friday.")
