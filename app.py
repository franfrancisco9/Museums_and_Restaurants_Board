import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, jsonify
import datetime
import json

app = Flask(__name__)

selected_exhibitions_file = 'selected_exhibitions.json'

def get_unique_cities():
    cities = set()
    data_folder = './data'
    for file_name in os.listdir(data_folder):
        if 'exhibitions' in file_name or 'galleries' in file_name:
            city = file_name.split('_')[0]
            cities.add(city)
    return list(cities)

def load_data(file_name, city=None):
    data_path = f'./data/{file_name}.csv'
    try:
        df = pd.read_csv(data_path)
        if city and 'location' in df.columns:
            df = df[df['location'].str.lower() == city.lower()]
        return df.to_dict(orient='records')
    except FileNotFoundError:
        return []

def load_galleries():
    galleries = pd.read_csv('./data/london_galleries.csv')  # Adjust path as necessary
    return galleries.set_index('galery_name').to_dict(orient='index')

def process_exhibitions(exhibitions):
    valid_exhibitions = []
    for exhibition in exhibitions:
        time_period = exhibition.get('time_period', '')
        if time_period:
            try:
                dates = time_period.strip().split('-')
                dates[0] = dates[0].strip().split()[0] + ' ' + dates[0].strip().split()[1]
                dates[1] = dates[1].strip().split()[0] + ' ' + dates[1].strip().split()[1]
                year = time_period.split()[-1]
                dates = [f'{date} {year}' for date in dates]
            except IndexError:
                dates = []
            if len(dates) == 2:
                try:
                    start_date = datetime.datetime.strptime(dates[0].strip(), "%d %b %Y").date()
                    end_date = datetime.datetime.strptime(dates[1].strip(), "%d %b %Y").date()
                    exhibition['start_date'] = start_date.isoformat()
                    exhibition['end_date'] = end_date.isoformat()
                except ValueError:
                    print(f"Error parsing dates for exhibition: {exhibition['exhibition_name']}")
            else:
                print(f"Invalid time period for exhibition: {exhibition['exhibition_name']}")
        
        # Ensure description is a string
        if 'exhibition_description' in exhibition:
            exhibition['exhibition_description'] = str(exhibition['exhibition_description'])
        
        valid_exhibitions.append(exhibition)
    return valid_exhibitions

def group_events_by_date(exhibitions):
    events_by_date = {}
    for exhibition in exhibitions:
        if 'start_date' in exhibition and exhibition['start_date']:
            date = exhibition['start_date']
            if date not in events_by_date:
                events_by_date[date] = []
            events_by_date[date].append(exhibition)

    condensed_events = []
    for date, events in events_by_date.items():
        if len(events) > 3:
            events_sorted = sorted(events, key=lambda x: x['exhibition_name'])
            titles = ', '.join([e['exhibition_name'] for e in events_sorted])
            condensed_events.append({
                'title': titles,
                'start': date,
                'end': date,
                'id': 'exhibition-' + str(exhibitions.index(events_sorted[0]) + 1)  # Link to the first event of the day
            })
        else:
            for event in events:
                condensed_events.append({
                    'title': event['exhibition_name'],
                    'start': event['start_date'],
                    'end': event['end_date'],
                    'id': 'exhibition-' + str(exhibitions.index(event) + 1)
                })
    return condensed_events

def group_events_by_planned_dates(exhibitions):
    events = []
    for exhibition in exhibitions:
        if 'planned_dates' in exhibition and exhibition['planned_dates']:
            for date in exhibition['planned_dates']:
                start = date.split(' - ')[0].strip()
                end = date.split(' - ')[1].strip()
                events.append({
                    'title': exhibition['exhibition_name'],
                    'start': start,
                    'end': end,
                    'id': 'exhibition-' + str(exhibitions.index(exhibition) + 1)
                })
    return events

def save_selected_exhibitions(exhibitions):
    # save dictionaries to json file
    with open(selected_exhibitions_file, 'w') as f:
        json.dump(exhibitions, f)
        
def load_selected_exhibitions():
    # load dictionaries from json file
    try:
        with open(selected_exhibitions_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

@app.route('/')
def index():
    cities = sorted(get_unique_cities())
    selected_exhibitions = load_selected_exhibitions()
    
    # Ensure all fields in selected exhibitions are properly defined
    for exhibition in selected_exhibitions:
        exhibition['exhibition_description'] = str(exhibition.get('exhibition_description', ''))
        exhibition['planned_dates'] = exhibition.get('planned_dates', [])

    events = group_events_by_planned_dates(selected_exhibitions)

    return render_template('index.html', cities=cities, exhibitions=selected_exhibitions, events=events)


@app.route('/restaurants')
def show_restaurants():
    city = request.args.get('city', 'london')
    restaurants = load_data('restaurants', city=city)
    return render_template('restaurants.html', city=city.capitalize(), restaurants=restaurants)

@app.route('/exhibitions')
def show_exhibitions():
    city = request.args.get('city', 'london')
    gallery = request.args.get('gallery', None)
    exhibitions = load_data(f'{city}_exhibitions')
    galleries = load_galleries()
    valid_exhibitions = process_exhibitions(exhibitions)
    if gallery:
        valid_exhibitions = [e for e in valid_exhibitions if e.get('galery_name') == gallery]
    for exhibition in valid_exhibitions:
        gallery_name = exhibition.get('galery_name')
        if gallery_name in galleries:
            exhibition['gallery_img'] = galleries[gallery_name]['gallery_imgs'].strip('[]').replace('"', '').split(',')[0] if galleries[gallery_name]['gallery_imgs'] else ''
    condensed_events = group_events_by_date(valid_exhibitions)
    return render_template('exhibitions.html', city=city.capitalize(), exhibitions=valid_exhibitions, condensed_events=condensed_events, galleries=galleries)

@app.route('/select_exhibition', methods=['POST'])
def select_exhibition():
    exhibition = request.form.get('exhibition')
    planned_dates = request.form.get('planned_dates')
    exhibition = json.loads(exhibition)
    exhibition['planned_dates'] = planned_dates.split(',')
    selected_exhibitions = load_selected_exhibitions()
    selected_exhibitions.append(exhibition)
    save_selected_exhibitions(selected_exhibitions)
    return redirect(url_for('index'))

@app.route('/remove_exhibition', methods=['POST'])
def remove_exhibition():
    exhibition = request.form.get('exhibition')
    exhibition = json.loads(exhibition)
    selected_exhibitions = load_selected_exhibitions()
    selected_exhibitions = [ex for ex in selected_exhibitions if ex['exhibition_name'] != exhibition['exhibition_name']]
    save_selected_exhibitions(selected_exhibitions)
    return redirect(url_for('index'))

@app.route('/update_planned_dates', methods=['POST'])
def update_planned_dates():
    exhibition_name = request.form.get('exhibition_name')
    new_dates = request.form.get('new_dates').split(',')
    selected_exhibitions = load_selected_exhibitions()
    for exhibition in selected_exhibitions:
        if exhibition['exhibition_name'] == exhibition_name:
            exhibition['planned_dates'] = new_dates
            break
    save_selected_exhibitions(selected_exhibitions)
    return redirect(url_for('index'))

@app.route('/galleries')
def show_galleries():
    city = request.args.get('city', 'london')
    galleries = load_data(f'{city}_galleries')
    return render_template('galleries.html', city=city.capitalize(), galleries=galleries)

if __name__ == '__main__':
    app.run(debug=True)
