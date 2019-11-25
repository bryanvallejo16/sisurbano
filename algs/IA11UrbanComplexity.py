# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Sisurbano
                                 A QGIS plugin
 Cáculo de indicadores urbanos
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-10-01
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
__date__ = '2019-11-12'
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
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSink)
from .ZProcesses import *
from .Zettings import *
from .ZHelpers import *
import numpy as np
import pandas as pd
import tempfile

pluginPath = os.path.split(os.path.split(os.path.dirname(__file__))[0])[0]

class IA11UrbanComplexity(QgsProcessingAlgorithm):
    """
    Mide simultáneamente la diversidad y frecuencia de usos terciarios (personas jurídicas)
    en el territorio, a través de la fórmula de Shannon proveniente de la Teoría de la Información.
    Formula: Σj Shannon - Ìndice de diversidad de Wienner
    """
    TERTIARYUSES = 'TERTIARYUSES'
    BLOCKS = 'BLOCKS'
    FIELD_POPULATION = 'FIELD_POPULATION'
    FIELD_ACTIVITIES = 'FIELD_ACTIVITIES'
    CELL_SIZE = 'CELL_SIZE'    
    OUTPUT = 'OUTPUT'
    STUDY_AREA_GRID = 'STUDY_AREA_GRID'    
    FULL_PATH = 'FULL_PATH'
    CURRENT_PATH = 'CURRENT_PATH'

    def initAlgorithm(self, config):
        currentPath = getCurrentPath(self)
        self.CURRENT_PATH = currentPath
        self.FULL_PATH = buildFullPathName(currentPath, nameWithOuputExtension(NAMES_INDEX['IA11'][1]))            

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.BLOCKS,
                self.tr('Manzanas'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )   

        # self.addParameter(
        #     QgsProcessingParameterField(
        #         self.FIELD_POPULATION,
        #         self.tr('Población'),
        #         'poblacion', 'BLOCKS'
        #     )
        # )         

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
            QgsProcessingParameterFeatureSource(
                self.TERTIARYUSES,
                self.tr('Uos terciarios (comercio, servicios u oficinas)'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_ACTIVITIES,
                self.tr('Actividades'),
                'actividad_', 'TERTIARYUSES'
            )
        )  


        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Salida'),
                QgsProcessing.TypeVectorAnyGeometry,
                str(self.FULL_PATH)                
            )
        )

    def processAlgorithm(self, params, context, feedback):
      steps = 0
      totalStpes = 3
      # fieldPopulation = params['FIELD_POPULATION']
      fieldActivities = str(params['FIELD_ACTIVITIES'])

      feedback = QgsProcessingMultiStepFeedback(totalStpes, feedback)

      steps = steps+1
      feedback.setCurrentStep(steps)
      if not OPTIONAL_GRID_INPUT: params['CELL_SIZE'] = P_CELL_SIZE
      grid, isStudyArea = buildStudyArea(params['CELL_SIZE'], params['BLOCKS'],
                                         params['STUDY_AREA_GRID'],
                                         context, feedback)
      gridNeto = grid  


      tempOutput = self.CURRENT_PATH+'/zaux.shp'

      # print(QgsProcessing.TEMPORARY_OUTPUT)

      steps = steps+1
      feedback.setCurrentStep(steps)
      activitiesGrid = joinAttrByLocation(params['TERTIARYUSES'],
                              gridNeto['OUTPUT'],
                              ['id_grid'],
                              [INTERSECTA],
                              UNDISCARD_NONMATCHING,               
                              context,
                              feedback, tempOutput)    

      # steps = steps+1
      # feedback.setCurrentStep(steps)
      # rep = calculateField(gridNeto['OUTPUT'], 'id_ter', '$id', context,
      #                               feedback, type=1)      
                                   
      activitiesLayer =  QgsVectorLayer(tempOutput, "activitiesGrid", "ogr")   

      # activitiesLayer = convertTempOuputToObject(activitiesGrid)


      # layer = self.parameterAsVectorLayer(params, activitiesLayer, context)
      layer = activitiesLayer
      # layer = activitiesGrid
      features = layer.getFeatures()
      # fields = layer.dataProvider().fields()
      field_names = [field.name() for field in layer.fields()]
      # print(field_names)
      # print(len(features))

      df = pd.DataFrame(features, columns = field_names)

      # df["id_grid"]= df["id_grid"].astype(int) 

      aggregation = {
        fieldActivities : {
          'amount_class':'count'
        }
      }

      grouped = df.groupby(['id_grid',fieldActivities]).agg(aggregation)
      grouped.columns = grouped.columns.droplevel(level=0)

      aggregation = {
        fieldActivities : {
          'total_class':'count' # conteo de todos los puntos
          # 'total_class':'nunique' # conteo de los puntos no repetidos
        }
      }

      grouped2 = df.groupby(['id_grid']).agg(aggregation)
      grouped2.columns = grouped2.columns.droplevel(level=0)


      res = grouped.join(grouped2).reset_index()

      print(res['amount_class'])
      print(res)

      uniqueActivities = pd.unique(df[fieldActivities])
      totalActivities = len(uniqueActivities)
      res["total_study"] = totalActivities


      # cross = pd.crosstab(df['id'], df[fieldActivities])
      res["proporcion"] = ((res['amount_class'] / res['total_class']) * np.log(res['amount_class'] / res['total_class']))
      aggregation = {
        'proporcion' : {
          'shannon':'sum'
        }
      }   

      res = res.groupby(['id_grid']).agg(aggregation)
      res.columns = res.columns.droplevel(level=0)
      res['shannon'] = res['shannon'] * -1



      outputCsv = self.CURRENT_PATH+'/sett_shannon.csv'

      feedback.pushConsoleInfo(str(('Settings shannon en ' + outputCsv)))    
      # res.to_csv(outputCsv, sep = ";", encoding='utf-8')
      res.to_csv(outputCsv)


      print(res)


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
      formulaDummy = 'to_string(id_grid)'
      gridDummy = calculateField(gridNeto['OUTPUT'],
                                 'griid',
                                 formulaDummy,
                                 context,
                                 feedback, QgsProcessing.TEMPORARY_OUTPUT, 2)      



      steps = steps+1
      feedback.setCurrentStep(steps)
      gridShannon = joinByAttr2(gridDummy['OUTPUT'], 'griid',
                                outputCsv, 'id_grid',
                                'shannon',
                                UNDISCARD_NONMATCHING,
                                '',
                                1,
                                context,
                                feedback)


      steps = steps+1
      feedback.setCurrentStep(steps)
      formulaDummy = 'shannon * 1'
      result = calculateField(gridShannon['OUTPUT'],
                                 NAMES_INDEX['IA11'][0],
                                 formulaDummy,
                                 context,
                                 feedback, params['OUTPUT'])            

      # gridShannon = joinByAttr(r'/Users/terra/llactalab/data/SHAPES_PARA_INDICADORES/SIS-OUTPUTS/ia11.shp', 'id_grid',
      #                           '/Users/terra/llactalab/data/SHAPES_PARA_INDICADORES/SIS-OUTPUTS/sett_shannon.csv', 'id_grid',
      #                           ['shannon'],
      #                           UNDISCARD_NONMATCHING,
      #                           '',
      #                           1,
      #                           context,
      #                           feedback, params['OUTPUT'])

      # res.iloc[1:, [4]] = res.iloc[1:, [2]] / res.iloc[1:, [3]]
  





      # print(totalActivities)
      # print(grouped)
      # print(grouped2)


      # print(un)
      # print(cross)



      # print(df[fieldActivities])

      return result


    def icon(self):
        return QIcon(os.path.join(pluginPath, 'sisurbano', 'icons', 'complex.png'))

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'A11 Complejidad urbana'

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
        return 'A Ambiente construido'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return IA11UrbanComplexity()

