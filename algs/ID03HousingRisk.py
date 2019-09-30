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
__date__ = '2019-09-16'
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

pluginPath = os.path.split(os.path.split(os.path.dirname(__file__))[0])[0]

class ID03HousingRisk(QgsProcessingAlgorithm):
    """
    Mide le porcentaje de viviendas ubicadas cerca de vertederos, camales,
    plantas de tratamiento de agua, industria pesada, zonas de deslizamiento,
    propensas a inundaciones, entre otros factores que influyen sobre el
    estado de la salud y las condiciones de vida.
    La cantidad de unidades de vivienda en el área urbana emplazadas en
    zonas vulnerables y de riesgo, dividido para el total de unidades de
    vivienda en el área urbana a evaluar    
    Formula: (N° de viviendasen zona de riesgo / total de viviendas)*100
    """
    BLOCKS = 'BLOCKS'
    # FIELD_POPULATION = 'FIELD_POPULATION'
    FIELD_HOUSING = 'FIELD_HOUSING'
    RISK = 'RISK'
    CELL_SIZE = 'CELL_SIZE'    
    OUTPUT = 'OUTPUT'


    def initAlgorithm(self, config):
        currentPath = getCurrentPath(self)
        FULL_PATH = buildFullPathName(currentPath, nameWithOuputExtension(NAMES_INDEX['ID03'][1]))           


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
            QgsProcessingParameterField(
                self.FIELD_HOUSING,
                self.tr('Viviendas'),
                'viviendas', 'BLOCKS'
            )
        )         

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
                self.RISK,
                self.tr('Zonas de riesgo'),
                [QgsProcessing.TypeVectorAnyGeometry]
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
      totalStpes = 13
      # fieldPopulation = params['FIELD_POPULATION']
      fieldHousing = params['FIELD_HOUSING']

      feedback = QgsProcessingMultiStepFeedback(totalStpes, feedback)

      """
      -----------------------------------------------------------------
      Calcular las facilidades a espacios pubicos abiertos
      -----------------------------------------------------------------
      """

      steps = steps+1
      feedback.setCurrentStep(steps)
      blocksWithId = calculateField(params['BLOCKS'], 'id_block', '$id', context,
                                    feedback, type=1)

      steps = steps+1
      feedback.setCurrentStep(steps)
      riskWithId = calculateField(params['RISK'], 'idx', '$id', context,
                                      feedback, type=1)      

      # ME QUEDO CON LOS TIENEN RIESGO
      steps = steps+1
      feedback.setCurrentStep(steps)
      counterRisk = joinByLocation(blocksWithId['OUTPUT'],
                                    riskWithId['OUTPUT'],
                                    'idx', [INTERSECTA], [COUNT],
                                    DISCARD_NONMATCHING,
                                    context,
                                    feedback)
 

      steps = steps+1
      feedback.setCurrentStep(steps)
      blocksJoined = joinByAttr(blocksWithId['OUTPUT'], 'id_block',
                                counterRisk['OUTPUT'], 'id_block',
                                [],
                                UNDISCARD_NONMATCHING,
                                'rk_',
                                context,
                                feedback)

      """
      -----------------------------------------------------------------
      Calcular numero de viviendas por hexagano
      -----------------------------------------------------------------
      """
      steps = steps+1
      feedback.setCurrentStep(steps)
      grid = createGrid(params['BLOCKS'], params['CELL_SIZE'], context,
                        feedback)    

      # Eliminar celdas efecto borde
      gridNeto = grid

      steps = steps+1
      feedback.setCurrentStep(steps)
      gridNeto = calculateField(gridNeto['OUTPUT'], 'id_grid', '$id', context,
                                feedback, type=1)

      steps = steps+1
      feedback.setCurrentStep(steps)
      segments = intersection(blocksJoined['OUTPUT'], gridNeto['OUTPUT'],
                              [],
                              'id_grid',
                              context, feedback)

      # Haciendo el buffer inverso aseguramos que los segmentos
      # quden dentro de la malla
      steps = steps+1
      feedback.setCurrentStep(steps)
      riskForSegmentsFixed = makeSureInside(segments['OUTPUT'],
                                                  context,
                                                  feedback)
      # Con esto se saca el total de viviendas
      steps = steps+1
      feedback.setCurrentStep(steps)
      gridNetoAndSegments = joinByLocation(gridNeto['OUTPUT'],
                                           riskForSegmentsFixed['OUTPUT'],
                                           'rk_' + fieldHousing + ';' + fieldHousing,
                                           [CONTIENE], [SUM], DISCARD_NONMATCHING,                 
                                           context,
                                           feedback)



      steps = steps+1
      feedback.setCurrentStep(steps)
      formulaProximity = '(coalesce(rk_'+fieldHousing+'_sum,0) /  coalesce('+fieldHousing+'_sum,0))*100'
      riskHousing = calculateField(gridNetoAndSegments['OUTPUT'], NAMES_INDEX['ID03'][0],
                                        formulaProximity,
                                        context,
                                        feedback, params['OUTPUT'])

      return riskHousing


        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        #return {self.OUTPUT: dest_id}

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'sisurbano', 'icons', 'riesgo.png'))

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'D03 Viviendas emplazadas en zonas vulnerables y de riesgo'

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
        return 'D Dinámicas Socio-espaciales'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ID03HousingRisk()

