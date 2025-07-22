import pandas as pd
import itertools
import random
from datetime import datetime, timedelta
from collections import defaultdict

# Configurable semester dates
start_date = datetime(2025, 8, 18)
end_date = datetime(2025, 12, 19)
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Load class and teacher data
classes = pd.read_csv('data/classes.csv')
teachers = pd.read_csv('data/teachers.csv')
with open('data/lessons.txt', 'r') as f:
    lessons = [line.strip() for line in f if line.strip()]

# Parse and clean inputs
teachers['AvailableDays'] = teachers['AvailableDays'].str.split(',')
classes['MeetingDays'] = classes['MeetingDays'].str.split(',')

# Create list of all dates in the semester
semester_dates = pd.date_range(start=start_date, end=end_date, freq='D')
weekday_map = {day: i for i, day in enumerate(WEEKDAYS)}

# Generate class sessions with actual dates
class_sessions = []
for _, cls in classes.iterrows():
    for date in semester_dates:
        if date.strftime('%A') in cls['MeetingDays']:
            class_sessions.append({
                'Date': date,
                'ClassName': cls['ClassName'],
                'Time': cls['Time'],
                'Location': cls['Location'],
                'Week': date.isocalendar().week
            })

# Shuffle lessons and prepare state
lesson_pool = itertools.cycle(lessons)
assigned_teachers = defaultdict(lambda: defaultdict(lambda: {'days': set(), 'count': 0}))
teacher_lessons_by_week = defaultdict(dict)
schedule = []

# Assign teachers and lessons
for session in class_sessions:
    day_name = session['Date'].strftime('%A')
    week = session['Week']

    def get_available(rank):
        return [
            t for _, t in teachers[teachers['Rank'] == rank].iterrows()
            if day_name in t['AvailableDays'] and
               assigned_teachers[t['Name']][week]['count'] < t['MaxClassesPerWeek'] and
               day_name not in assigned_teachers[t['Name']][week]['days']
        ]

    lead_options = get_available('Lead')
    assist_options = get_available('Assistant')

    if not lead_options or not assist_options:
        print(f"⚠️ Skipping {session['ClassName']} on {session['Date'].strftime('%Y-%m-%d')}: no teacher pair")
        continue

    lead = random.choice(lead_options)
    assistant = random.choice([a for a in assist_options if a['Name'] != lead['Name']])

    # Assign lesson for that week if not already chosen
    for t in (lead, assistant):
        if week not in teacher_lessons_by_week[t['Name']]:
            teacher_lessons_by_week[t['Name']][week] = next(lesson_pool)

    lesson = teacher_lessons_by_week[lead['Name']][week]  # Lead lesson determines class lesson

    schedule.append({
        'Date': session['Date'].strftime('%Y-%m-%d'),
        'Weekday': day_name,
        'ClassName': session['ClassName'],
        'Time': session['Time'],
        'Location': session['Location'],
        'LeadTeacher': lead['Name'],
        'AssistantTeacher': assistant['Name'],
        'Lesson': lesson
    })

    # Update weekly state
    for t in (lead, assistant):
        assigned_teachers[t['Name']][week]['days'].add(day_name)
        assigned_teachers[t['Name']][week]['count'] += 1

# Save to Excel
df_schedule = pd.DataFrame(schedule)
df_schedule.sort_values(by=['Date', 'Time'], inplace=True)
df_schedule.to_excel('output/semester_schedule.xlsx', index=False)

print("✅ Semester schedule saved to 'semester_schedule.xlsx'")
