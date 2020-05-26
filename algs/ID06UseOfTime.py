# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Sisurbano
                                 A QGIS plugin
 Cáculo de indicadores urbanos
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-09-16
        copyright            : (C) 2019 by LlactaLAB
        email                : johnatan.astudillo@ucuenca.edu.ec
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Johnatan Astudillo'
__date__ = '2020-01-23'
__copyright__ = '(C) 2019 by LlactaLAB'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.core import (QgsProcessing,
                       QgsProcessingMultiStepFeedback,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSink)
from .ZProcesses import *
from .Zettings import *
from .ZHelpers import *
import numpy as np
import pandas as pd
import tempfile
import subprocess
import datetime

pluginPath = os.path.split(os.path.split(os.path.dirname(__file__))[0])[0]

class ID06UseOfTime(QgsProcessingAlgorithm):
    """
    Informa sobre la asignación semanal de tiempo de la población de 12 años
    y más para actividades personales (actividades no remuneradas para otros
    hogares, para la comunidad, trabajo voluntario; esparcimiento y cultura; familia y sociabilidad)
    de lunes a viernes.
    Formula: Promedio del tiempo semanal en horas que los miembros del
    hogar de 12 años o más utilizaron para actividades personales.
    """

    BLOCKS = 'BLOCKS'
    DPA_SECTOR = 'DPA_SECTOR'
    ENCUESTA = 'ENCUESTA'
    CELL_SIZE = 'CELL_SIZE'
    OUTPUT = 'OUTPUT'
    STUDY_AREA_GRID = 'STUDY_AREA_GRID'
    CURRENT_PATH = 'CURRENT_PATH'    

    def initAlgorithm(self, config):
        currentPath = getCurrentPath(self)
        self.CURRENT_PATH = currentPath        
        FULL_PATH = buildFullPathName(currentPath, nameWithOuputExtension(NAMES_INDEX['ID06'][1]))

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.BLOCKS,
                self.tr('Zonas Censales'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.DPA_SECTOR,
                self.tr('DPA Zona'),
                'dpa_zona', 'BLOCKS'
            )
        )           


        self.addParameter(
            QgsProcessingParameterFile(
                self.ENCUESTA,
                self.tr('Encuesta específica de uso del tiempo'),
                extension='csv',
                defaultValue=''
            )
        )           

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.STUDY_AREA_GRID,
                self.tr(TEXT_GRID_INPUT),
                [QgsProcessing.TypeVectorPolygon],
                '', OPTIONAL_GRID_INPUT
            )
        )


        if OPTIONAL_GRID_INPUT:
            self.addParameter(
                QgsProcessingParameterNumber(
                    self.CELL_SIZE,
                    self.tr('Tamaño de la malla'),
                    QgsProcessingParameterNumber.Integer,
                    P_CELL_SIZE, False, 1, 99999999
                )
            )          


        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Salida'),
                QgsProcessing.TypeVectorAnyGeometry,
                str(FULL_PATH)
            )
        )
        

    def processAlgorithm(self, params, context, feedback):
        steps = 0
        totalStpes = 17
        fieldDpa = params['DPA_SECTOR']
        # fieldHab = params['NUMBER_HABITANTS']

        feedback = QgsProcessingMultiStepFeedback(totalStpes, feedback)

        if not OPTIONAL_GRID_INPUT: params['CELL_SIZE'] = P_CELL_SIZE
        grid, isStudyArea = buildStudyArea(params['CELL_SIZE'], params['BLOCKS'],
                                         params['STUDY_AREA_GRID'],
                                         context, feedback)
        gridNeto = grid  


        steps = steps+1
        feedback.setCurrentStep(steps)

        path = params['ENCUESTA']

        file = path

        #p03 edad
        cols = ['id_hogar', 'P03', 
                'UT98A', 'UT98B', 'UT99A', 'UT99B', 'UT100A', 'UT100B', 
                'UT101A', 'UT101B', 'UT102A', 'UT102B', 'UT103A', 'UT103B', 'UT104A',
                'UT104B', 'UT105A', 'UT105B', 'UT106A', 'UT106B', 'UT107A', 'UT107B', 
                'UT108A','UT108B', 'UT109A','UT109B', 'UT110A', 'UT110B', 'UT111A', 
                'UT111B', 'UT112A', 'UT112B', 'UT113A','UT113B', 'UT114A','UT114B',
                'UT116A', 'UT116B', 'UT117A', 'UT117B', 'UT118A', 'UT118B', 'UT119A', 
                'UT119B', 'UT120A','UT120B', 'UT121A', 'UT121B', 'UT122A', 'UT122B']

        df = pd.read_csv(file, usecols=cols)

        df['id_hogar'] = df['id_hogar'].astype(str)
        df['P03'] = df['P03'].astype(str)

        df.loc[df['id_hogar'].str.len() == 14, 'id_hogar'] = "0" + df['id_hogar']
        df['codsec'] = df['id_hogar'].str[0:12]
        df['codzon'] = df['id_hogar'].str[0:9]

        df = df[(df['P03'] >= '12')]

        fieldTimes = cols[2:]
        fildTimesRename = []

        # print(fieldTimes[:])

        for fieldTime in fieldTimes:
            df.loc[(df[fieldTime] == ' '), fieldTime] = "00"
            df[fieldTime] = df[fieldTime].astype(int)
            timerSplit = fieldTime.split('A')
            newName = timerSplit[0]
            isA = len(timerSplit) == 2
            indexElement = fieldTimes.index(fieldTime)
            if isA: 
                nameB = newName + "B"
                df.loc[(df[nameB] == ' '), nameB] = "00"
                df[newName] = df[fieldTime].astype(str) + ":" + df[nameB].astype(str) + ":00"
                fildTimesRename.append(newName) 


        df['sumTime'] = datetime.timedelta() 

        for field in fildTimesRename:
            df[field] = pd.to_timedelta(df[field])
            df['sumTime'] = df['sumTime'] + df[field]


        df['hours'] = df['sumTime'].dt.total_seconds() / 3600
        df['hours'] = df['hours'].astype(float)

        aggOptions = {
                      'codzon' : 'first',
                      'hours' : 'mean',
                     } 

        resSectores = df.groupby('codzon').agg(aggOptions)
    

        df = resSectores   
                  
        steps = steps+1
        feedback.setCurrentStep(steps)

        outputCsv = self.CURRENT_PATH+'/usoTiempo.csv'
        feedback.pushConsoleInfo(str(('usoTiempo en ' + outputCsv)))    
        df.to_csv(outputCsv, index=False)

        steps = steps+1
        feedback.setCurrentStep(steps)

        exitCsv = os.path.exists(outputCsv)
        if(exitCsv):
            print("El archivo CSV existe")
        else:
            print("No se encuentra CSV")

        CSV =  QgsVectorLayer(outputCsv, "csv", "ogr") 
        featuresCSV = CSV.getFeatures()
        # fields = layer.dataProvider().fields()
        field_names = [field.name() for field in CSV.fields()]       
        print(field_names)            


        steps = steps+1
        feedback.setCurrentStep(steps)
        result = joinByAttr2(params['BLOCKS'], fieldDpa,
                                outputCsv, 'codzon',
                                [],
                                UNDISCARD_NONMATCHING,
                                '',
                                1,
                                context,
                                feedback)

        # steps = steps+1
        # feedback.setCurrentStep(steps)
        # expressionNotNull = "des IS NOT '' AND des is NOT NULL"    
        # result =   filterByExpression(result['OUTPUT'], expressionNotNull, context, feedback) 



        steps = steps+1
        feedback.setCurrentStep(steps)
        formulaDummy = 'hours * 1.0'
        result = calculateField(result['OUTPUT'], 
                                 'hours_n',
                                 formulaDummy,
                                 context,
                                 feedback)  

 
        steps = steps+1
        feedback.setCurrentStep(steps)
        gridNeto = joinByLocation(gridNeto['OUTPUT'],
                             result['OUTPUT'],
                             ['hours_n'],                                   
                              [INTERSECTA], [MEDIA],
                              UNDISCARD_NONMATCHING,
                              context,
                              feedback)         
 

        fieldsMapping = [
            {'expression': '"id_grid"', 'length': 10, 'name': 'id_grid', 'precision': 0, 'type': 4}, 
            {'expression': '"area_grid"', 'length': 16, 'name': 'area_grid', 'precision': 3, 'type': 6}, 
            {'expression': '"hours_n_mean"', 'length': 20, 'name': NAMES_INDEX['ID06'][0], 'precision': 2, 'type': 6}
        ]      
        
        steps = steps+1
        feedback.setCurrentStep(steps)
        result = refactorFields(fieldsMapping, gridNeto['OUTPUT'], 
                                context,
                                feedback, params['OUTPUT'])                                                                

        return result
          
    def icon(self):
        return QIcon(os.path.join(pluginPath, 'sisurbano', 'icons', 'timer3.png'))

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'D06 Uso del tiempo'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'D Dinámicas socio-espaciales'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ID06UseOfTime()

    def shortHelpString(self):
        return  "<b>Descripción:</b><br/>"\
                "<span>Informa sobre la asignación semanal de tiempo de la población de 12 años y más para actividades personales (actividades no remuneradas para otros hogares, para la comunidad, trabajo voluntario; esparcimiento y cultura; familia y sociabilidad) de lunes a viernes.</span>"\
                "<br/><br/><b>Justificación y metodología:</b><br/>"\
                "<span></span>"\
                "<br/><br/><b>Formula:</b><br/>"\
                "<span>Promedio del tiempo semanal en horas que los miembros del hogar de 12 años o más utilizaron para actividades personales.</span><br/>"