import pandas as pd
from opencage.geocoder import OpenCageGeocode
import folium
from geopy import distance
from flask import Flask, render_template, request
import os

#PATH = os.path.dirname(os.path.abspath(__file__))  # para deploy

app = Flask(__name__)

gymy = pd.DataFrame()

def token(tokenfile):
    with open(tokenfile, 'r') as f:
        t=f.readlines()[0].split('\n')[0]
    return t

def filtro(string,form_user_input):
    for s in string.split(', '):
        if s in form_user_input:
            return True
    return False

#antes del primer request se cargan los datos
@app.before_first_request
def startup():
    global gymy
    gymy = pd.read_csv('csv/gymy_final.csv')
    #gymy = pd.read_csv(PATH+'/data/gymy_final.csv', delimiter =',') -> For pythonanywhere
    gymy['latlong'] = list(zip(gymy.lat, gymy.long))


@app.route('/', methods = ['POST','GET'])
def main():
    if request.method=='POST':
        try:
            filtro_usuario = request.form.get('dropdown')
            input_user = request.form['input_usuario']
            #inicializo GeoCage para localizar input del usuario
            tokengeo = token('geocagetoken.txt')
            #tokengeo = token(PATH+'/geocagetoken.txt') -> For pythonanywhere
            geocoder = OpenCageGeocode(tokengeo)
            results = geocoder.geocode(input_user)
            kmeters = 2
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
            fcoordinates.append(input_user)

            #se separa la string
            latlong = fcoordinates[0]
            radio = fcoordinates[1]
            localidad = fcoordinates[2]
            direccion_solicitud = fcoordinates[3]

            

            gymy_modelo = gymy.copy()

            if filtro_usuario != 'Todas las categorías':
                gymy_modelo['filtro'] = gymy_modelo.category.apply(filtro, form_user_input=filtro_usuario)
            else:
                gymy_modelo['filtro'] = True

            gymy_modelo = gymy_modelo[gymy_modelo.filtro==True]

            gymy_modelo['distance'] = gymy_modelo.latlong.apply(lambda x , y=latlong : distance.distance(x, y).km)
            display_df = gymy_modelo[gymy_modelo.distance<radio]
            display_df.reset_index(inplace=True)
            n_gyms = len(display_df)

            if n_gyms>0:
                #creating map object
                tooltip = 'Location you chose: {} \n {}'.format(direccion_solicitud,localidad)
                mapa=folium.Map(latlong, zoom_start=15, width='100%', height='70%')
                folium.Marker(latlong, tooltip=tooltip, icon=folium.Icon()).add_to(mapa)
                for i in range(len(display_df)):
                    htmlpopup="""
                            <font face = Verdana size = "1"> <label ><b>{}</b></label> <br> </font>
                            <p>
                            <font face= Verdana size = "1"><label><b> Teléfono:</b> {}</label> <br>
                            <label><b>Dirección:</b> {}</label> <br>
                            <label><b>Web:</b> {}</label> <br>
                            <label><b>Categorías: </b>{}</label>
                            </font>
                                </p>
                            """.format(display_df.names[i],display_df.phone[i],display_df.address[i],
                                    display_df.web[i],display_df.category[i])

                            
                    iframe = folium.IFrame(html=htmlpopup, width=225, height=125)
                    popup = folium.Popup(iframe)

                    folium.Marker([display_df.lat[i],display_df.long[i]], popup=popup, 
                                tooltip = display_df.names[i], icon = folium.Icon(color='red')).add_to(mapa)
                mapa.save('templates/{}.html'.format(direccion_solicitud))
                #mapa.save(PATH+'/templates/{}.html'.format(direccion_solicitud))  -> For pythonanywhere

                devuelta =  'Existen {} GYMYs cerca de {}'.format(n_gyms,direccion_solicitud)

                #agrega el jinja de block al html de folium
                with open('templates/{}.html'.format(direccion_solicitud), 'a') as f:
                #with open(PATH+'/templates/{}.html'.format(direccion_solicitud), 'a') as f: -> For pythonanywhere
                    f.write('\n{% block content %} {% endblock %}')

                return render_template('index.html' , gyms_template = devuelta, 
                                        mapatrue = '{}.html'.format(direccion_solicitud), dropdown=filtro_usuario)
            
            else:
                devuelta = 'No hay Gymys cerca'
                return render_template('index.html' , gyms_template = devuelta , mapatrue = 'nomapa.html',
                                    dropdown='Todas las categorías')


                


        except:
            devuelta = 'Dirección Inválida. Prueba con otra'
            return render_template('index.html' , gyms_template = devuelta , mapatrue = 'nomapa.html',
                                    dropdown='Todas las categorías')

    else:
        return render_template('index.html', gyms_template = '', mapatrue = 'nomapa.html', dropdown='Todas las categorías')
 


if __name__=='__main__':
    app.run(debug=True)

