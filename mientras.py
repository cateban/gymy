import re
import numpy as np
import pandas as pd
from opencage.geocoder import OpenCageGeocode
from tqdm import tqdm
from tqdm import trange
import folium
from folium import plugins
from geopy import distance
from flask import Flask, render_template, request
import io
import os

gymy = pd.read_csv('csv/gymy_latlong.csv')
gymy.drop(columns='Unnamed: 0', inplace=True)
gymy.head()

gymy['latlong'] = list(zip(gymy.lat, gymy.long))

#geocoder token reader
def token(tokenfile):
    with open(tokenfile, 'r') as f:
        t=f.readlines()[0].split('\n')[0]
    return t

geocoder = OpenCageGeocode(token('geocagetoken.txt'))


#Function that gets the lat long from user input
def getting_coor_latlong():
    try:
        user_input = input('¿Donde te gustaría ejercitarte? ')
        kmeters = 2
        results = geocoder.geocode(user_input)
        fcoordinates=[]
        coordinates=[]
        coordinates.append(results[0]['geometry']['lat']) 
        coordinates.append(results[0]['geometry']['lng'])
        country = results[0]['components']['country']
        city=results[0]['components']['city']
        localidad = country+', '+city
        fcoordinates.append(coordinates)
        fcoordinates.append(kmeters)
        fcoordinates.append(localidad)
        fcoordinates.append(user_input)
        return fcoordinates
    except:
        return 'Not a valid address'


def main_geopy():
    try:
        #user input to where the map is initializing
        coordenadas = getting_coor_latlong()
        latlong = coordenadas[0]
        radio = coordenadas[1]
        localidad = coordenadas[2]
        direccion_solicitud = coordenadas[3]

        gymy_modelo = gymy.copy()
        gymy_modelo['distance'] = gymy_modelo.latlong.apply(lambda x , y=latlong : distance.distance(x, y).km)
        display_df = gymy_modelo[gymy_modelo.distance<radio]
        display_df.reset_index(inplace=True)
        n_gyms = len(display_df)

        #creating map object
        tooltip = 'Location you chose: {} \n {}'.format(direccion_solicitud,localidad)
        mapa=folium.Map(latlong, zoom_start=15, width='70%', height='70%')
        folium.Marker(latlong, tooltip=tooltip, icon=folium.Icon()).add_to(mapa)
        for i in trange(len(display_df)):
            popup =''

            if str(display_df.phone[i]) != 'nan' :
                popup += 'Telefono: ' + str(display_df.phone[i])

            if str(display_df.address[i]) != 'nan' :
                popup += ' Direccion: '+str(display_df.address[i])

            if str(display_df.web[i]) != 'nan' :
                popup += ' Web: '+str(display_df.web[i])

            folium.Marker([display_df.lat[i],display_df.long[i]], popup=popup,
                            tooltip = display_df.names[i], icon = folium.Icon(color='red')).add_to(mapa)   
        print('Amount of gyms near {} are: {}'.format(direccion_solicitud,n_gyms))
        mapa.save('templates/MapaFinal.html')
        print(display_df)

    except:
        print('Dirección inválida, por favor ingresa otra dirección')

main_geopy()