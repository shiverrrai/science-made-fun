import streamlit as st
import pandas as pd
import itertools
import random
from datetime import datetime
from collections import defaultdict

st.title("After-School Class Scheduler")

st.markdown("Upload your input files:")

classes_file = st.file_uploader("Upload `classes.csv`", type="csv")
teachers_file = st.file_uploader("Upload `teachers.csv`", type="csv")
lessons_file = st.file_uploader("Upload `lessons.txt`", type="txt")

start_date = st.date_input("Semester Start Date", datetime(2025, 8, 18))
end_date = st.date_input("Semester End Date", datetime(2025, 12, 19))

if st.button("Generate Schedule"):
    if not (classes_file and teachers_file and lessons_file):
        st.warning("Please upload all files.")
    else:
        classes = pd.read_csv(classes_file)
        teachers = pd.read_csv(teachers_file)
        lessons = [line.decode("utf-8").strip() for line in
                   lessons_file.readlines() if line.strip()]

        teachers['AvailableDays'] = teachers['AvailableDays'].apply(
            lambda x: [d.strip() for d in x.split(',')])
        classes['MeetingDays'] = classes['MeetingDays'].apply(
            lambda x: [d.strip() for d in x.split(',')])

        semester_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        class_sessions = []

        for _, cls in classes.iterrows():
            for date in semester_dates:
                if date.strftime('%A') in cls['MeetingDays']:
                    class_sessions.append({
                        'Date': date,
                        'Week': date.isocalendar().week,
                        'Weekday': date.strftime('%A'),
                        'ClassName': cls['ClassName'],
                        'Time': cls['Time'],
                        'Location': cls['Location']
                    })

        assigned_teachers = defaultdict(
            lambda: defaultdict(lambda: {'days': set(), 'count': 0}))
        teacher_lessons_by_week = defaultdict(dict)
        lesson_pool = itertools.cycle(lessons)
        schedule = []

        for session in class_sessions:
            day = session['Weekday']
            week = session['Week']


            def get_available(rank):
                return [
                    t for _, t in teachers[teachers['Rank'] == rank].iterrows()
                    if day in t['AvailableDays'] and
                       assigned_teachers[t['Name']][week]['count'] < t[
                           'MaxClassesPerWeek'] and
                       day not in assigned_teachers[t['Name']][week]['days']
                ]


            leads = get_available('Lead')
            assists = get_available('Assistant')

            if not leads or not assists:
                continue

            lead = random.choice(leads)
            assist = random.choice(
                [a for a in assists if a['Name'] != lead['Name']])

            for t in (lead, assist):
                if week not in teacher_lessons_by_week[t['Name']]:
                    teacher_lessons_by_week[t['Name']][week] = next(lesson_pool)

            lesson = teacher_lessons_by_week[lead['Name']][week]

            schedule.append({
                'Date': session['Date'].strftime('%Y-%m-%d'),
                'Weekday': session['Weekday'],
                'ClassName': session['ClassName'],
                'Time': session['Time'],
                'Location': session['Location'],
                'LeadTeacher': lead['Name'],
                'AssistantTeacher': assist['Name'],
                'Lesson': lesson
            })

            for t in (lead, assist):
                assigned_teachers[t['Name']][week]['count'] += 1
                assigned_teachers[t['Name']][week]['days'].add(day)

        df_schedule = pd.DataFrame(schedule)

        if df_schedule.empty:
            st.warning(
                "⚠️ No schedule could be created. Please check constraints and input files.")
        else:
            st.success("✅ Schedule created!")
            st.dataframe(df_schedule)
            csv = df_schedule.to_csv(index=False).encode('utf-8')
            st.download_button("Download Schedule as CSV", csv,
                               "semester_schedule.csv", "text/csv")
