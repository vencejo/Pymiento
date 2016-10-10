# -*- coding: utf-8 -*-
#!/usr/bin/python

from SimpleCV import *
import numpy as np
import pygame
import os
import picamera
import pynter

# Valores dependientes del montaje experimental
longitudMaxAgujero = 150
areaAgujero = 1900 
rangoErrorArea = 1100
rangoErrorPinchazos = 40   

tarjetaCompletamenteInsertada = False
enDepuracion = False # Para activar los print, poner a False para hacer el programa mas rapido

# Las coordenadas de los agujeros dependen del montaje experimental
agujeros_coords =  {(30, 40):(4,0),  (110, 40):(4,1),  (190, 40):(4,2),  (280, 40):(4,3),  (370, 40):(4,4),  (450, 40):(4,5), \
                    (30, 127):(3,0), (110, 127):(3,1), (195, 127):(3,2), (280, 127):(3,3), (370, 127):(3,4), (450, 127):(3,5), \
                    (30, 209):(2,0), (110, 209):(2,1), (195, 213):(2,2), (276, 214):(2,3), (365, 211):(2,4), (450, 216):(2,5), \
                    (30, 353):(1,0), (110, 353):(1,1), (188, 358):(1,2), (271, 358):(1,3), (355, 358):(1,4), (443, 366):(1,5), \
                    (30, 430):(0,0), (110, 430):(0,1), (185, 435):(0,2), (266, 439):(0,3), (350, 442):(0,4), (437, 446):(0,5) }
 
def tomaFoto(filename, brillo=50,resolucion=(2592,1944),preview=False,modoExposicion='auto'):
	""" Toma una foto con los ajustes que se le pasan como parametros ,
	la guarda en el archivo filename y devuelve un objeto Image de la foto """
	if preview:
		print "capturing image"
		start = time.time()

	with picamera.PiCamera() as picam:
		if preview:
			picam.start_preview()
			time.sleep(1)
		picam.resolution = resolucion
		picam.brightness = brillo
		picam.exposure_mode = modoExposicion
		picam.capture(filename)
		if preview:
			picam.stop_preview()
	if preview:
		end = time.time()
		print "captured image in " + str(end-start) + " seconds"
	return Image(filename)
	                   
def arrayAlista(array):
    """ Transforma un array de numpy en una lista """
    lista = []
    for elem in array:
        lista.append(list(elem))
    return lista

def buscaAgujerosPinchados(pinchados):
	""" Devuelve en una lista las coordenadas (fila, columna) de los agujeros pinchados
		En el siguiente formato segun la tarjeta:
		
					col0 col1 col2 col3 col4 col5
				----------------------------------
		fila 4 ->  (4,0)					(4,5)
		fila 3 ->
		fila 2 ->
		fila 1 ->
		fila 0 ->  (0,0)					(0,5)
					*****Aqui van los logos******
	"""
	# Gestion Error experimental
	listaPinchados = list(tuple(elem) for elem in pinchados)
	coordsPinchados = []
	for coord in agujeros_coords:
		for pinchado in listaPinchados:
			if (abs(pinchado[0] - coord[0]) < rangoErrorPinchazos)and (abs(pinchado[1] - coord[1]) < rangoErrorPinchazos):
				coordsPinchados.append(coord)
	
	listaCoord = [agujeros_coords[p] for p in coordsPinchados]
	lista01 = [ "0" for i in range(25)]
	for coord in listaCoord:
		if coord[0] == 4:
			continue
		lista01[coord[0]*6+coord[1]+1] = '1'
		
	return  "".join(lista01)
	
                 
def reproduceSonidos(archivoWav):
	pygame.mixer.init()
	pygame.mixer.music.load(archivoWav)
	pygame.mixer.music.play()
	while pygame.mixer.music.get_busy() == True:
		continue

if enDepuracion:
	display = Display((1024,768))
	
# Ciclo principal del programa
while True:
	# Captura y tratamiento inicial de la imagen
	imgOriginal = tomaFoto('temp.jpg') 
	imgSinCortar = imgOriginal.resize(imgOriginal.width / 3, imgOriginal.height /3)
	img = imgSinCortar.crop(320,50, 480, 500) #330,50, 465, 500
	#img.live()
	# Deteccion de caracteristicas
	imgBin =  img.binarize(50).erode()
	blobs = imgBin.findBlobs()
	
	# Dibuja todos los blobs en rojo, luego pintaremos los buenos en verde,
	# con lo que los malos se quedaran en rojo
	blobs.draw(width=5, color = Color.RED)
	if enDepuracion:
		print "Valores de los Blobs antes del filtrado"
		print "Longitudes: ", blobs.length()
		print "Areas: ", blobs.area()
		print "Coordenadas", blobs.coordinates()
		print ""
	
	# Filtro que elimina los blobs muy grandes o muy pequennos
	if blobs:
		# Si hay un blob muy grande es que la tarjeta no ha sido completamente insertada
		tarjetaCompletamenteInsertada = True #np.all(blobs.length() <= longitudMaxAgujero)
		# Se filtran los blobs buscando los que tengan  area y longitud similar a agujeros
		condicionFiltro = (blobs.area() >= (areaAgujero - rangoErrorArea)) &  \
						  (blobs.area() <= (areaAgujero + rangoErrorArea)) 
		blobs = blobs.filter(condicionFiltro)
		
		if enDepuracion:
			print "Valores de los Blobs despues del filtrado"
			print "Longitudes: ", blobs.length()
			print "Areas: ", blobs.area()
			print "Coordenadas", blobs.coordinates()
			print ""
	else:
		if enDepuracion:
			print "No se han detectado blobs"
	
	if tarjetaCompletamenteInsertada and blobs:
		# Abajo hay que poner la ruta absoluta para luego no tener problemas
		# con el script que hace que el programa arranque desde el inicio
		reproduceSonidos("/home/pi/Pymiento/electronicping.wav") 
		# Dibuja los blobs "buenos" en verde
		blobs.draw(width=7, color = Color.GREEN)
		blobs.image = img
		#Correlaciona las coordenadas de los blobs con las prefijadas
		aleatoria = buscaAgujerosPinchados(arrayAlista(blobs.coordinates()))
		nombre_archivo = aleatoria + ".png"
		salida = pynter.pinta_cuadro(aleatoria)
		salida.save(nombre_archivo)

	else:
		nombre_archivo = "sinDeteccion.png"
		salida = pynter.pinta_cuadro("0000000000000000000000000")
		salida.save(nombre_archivo)
		print "No se han detectado agujeros" 
		
	# Muestra la imagen de los blobs en pantalla
	if enDepuracion:
		imgBin = imgBin.resize(1024,768)
		imgBin.save(display)
	else:
		display = Display((1024,768))
		imgAleatoria = Image(nombre_archivo).resize(1024,768)
		imgAleatoria.save(display)

	
	
