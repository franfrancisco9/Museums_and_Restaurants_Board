import pandas as pd
import os

# Load the exhibitions and galleries data
exhibitions_df = pd.read_csv('worldwide_exhibitions.csv')
galleries_df = pd.read_csv('worldwide_galleries.csv')

# Ensure the output directory exists
output_dir = '.'
os.makedirs(output_dir, exist_ok=True)

# Get unique cities from the exhibitions data
cities = exhibitions_df['city_name'].unique()

for city in cities:
    print("")
    # Filter exhibitions for the city
    city_exhibitions = exhibitions_df[exhibitions_df['city_name'] == city]

    # Find gallery names for the exhibitions in this city
    city_gallery_names = city_exhibitions['galery_name'].unique()

    # Filter galleries based on the gallery names
    city_galleries = galleries_df[galleries_df['galery_name'].isin(city_gallery_names)]

    # Save city-specific exhibitions and galleries to CSV files
    city_exhibitions.to_csv(f'{output_dir}/{city.lower()}_exhibitions.csv', index=False)
    city_galleries.to_csv(f'{output_dir}/{city.lower()}_galleries.csv', index=False)

print('City-specific CSV files have been created.')
