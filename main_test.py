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

#PATH = os.path.dirname(os.path.abspath(__file__))  # para deploy

app = Flask(__name__)

gymy = pd.DataFrame()

def token(tokenfile):
    with open(tokenfile, 'r') as f:
        t=f.readlines()[0].split('\n')[0]
    return t

#antes del primer request se cargan los datos
@app.before_first_request
def startup():
    global gymy
    gymy = pd.read_csv('csv/gymy_final.csv')
    gymy.drop(columns='Unnamed: 0', inplace=True)
    gymy['latlong'] = list(zip(gymy.lat, gymy.long))

        

@app.route('/', methods = ['POST','GET'])
def main():
    if request.method=='POST':

        results = [[14.5014303,-90.4886139],
                    2,
                    'Guatemala, Guatemala City',
                    'oakland mall guatemala']



        #inicializo GeoCage para localizar input del usuario
        #input_user = request.form['input_usuario']
        #results = geocoder.geocode(input_user)
        #kmeters = 2
        #fcoordinates=[]
        #coordinates=[]
        #coordinates.append(results[0]['geometry']['lat']) 
        #coordinates.append(results[0]['geometry']['lng'])
        #country = results[0]['components']['country']
        #city=results[0]['components']['city']
        #localidad = country+', '+city
        #fcoordinates.append(coordinates)
        #fcoordinates.append(kmeters)
        #fcoordinates.append(localidad)
        #fcoordinates.append(input_user)

        #se separa la string
        coordenadas = results
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
        tooltip = 'Localidad solicitada: {} \n {}'.format(direccion_solicitud,localidad)
        mapa=folium.Map(latlong, zoom_start=15, width='100%', height='70%')
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
        
        mapa.save('templates/{}.html'.format(direccion_solicitud))

        devuelta =  'Existen {} GYMYs cerca de {}'.format(n_gyms,direccion_solicitud)

        #agrega el jinja de block al html de folium
        with open('templates/MapaFinal.html', 'a') as f:
            f.write('\n{% block content %} {% endblock %}')

        return render_template('index.html' , gyms_template = devuelta , mapatrue = '{}.html'.format(direccion_solicitud)) 
    else:

        return render_template('index.html', gyms_template = '', mapatrue = 'nomapa.html') 


if __name__=='__main__':
    app.run(debug=True)

