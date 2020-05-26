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
__date__ = '2019-012-04'
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

class ID04OpenPublicSpacesNeedImprovement(QgsProcessingAlgorithm):
    """
    Mide el porcentaje de espacios públicos abiertos
    (parques, plazas, parques cívicos, parque infantil,
    campo deportivo, margen de agua, parque lineal, bulevards y mercados abiertos)
    que necesitan mejoras en cuanto a la estructura, mobiliario,
    vegetación en relación con el número total de espacios públicos.
    Formula: (Superficie de espacios públicos abiertos que necesitan mejoras en m2 / Superficie total de espacios públicos abiertos en m2)*100
    """
    OPEN_SPACE = 'OPEN_SPACE'
    SPACE2IMPROVEMENT = 'SPACE2IMPROVEMENT'
    CELL_SIZE = 'CELL_SIZE'    
    OUTPUT = 'OUTPUT'
    STUDY_AREA_GRID = 'STUDY_AREA_GRID'


    def initAlgorithm(self, config):

        currentPath = getCurrentPath(self)  
        FULL_PATH = buildFullPathName(currentPath, nameWithOuputExtension(NAMES_INDEX['ID04'][1]))        

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.OPEN_SPACE,
                self.tr('Espacios públicos abiertos'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.SPACE2IMPROVEMENT,
                self.tr('Espacios públicos abiertos que necesitan mejoras'),
                [QgsProcessing.TypeVectorAnyGeometry]
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
        totalStpes = 8
        # fieldPopulation = params['FIELD_POPULATION']
        # fieldHousing = params['FIELD_HOUSING']

        feedback = QgsProcessingMultiStepFeedback(totalStpes, feedback)

        steps = steps+1
        feedback.setCurrentStep(steps)
        if not OPTIONAL_GRID_INPUT: params['CELL_SIZE'] = P_CELL_SIZE        
        grid, isStudyArea = buildStudyArea(params['CELL_SIZE'], params['OPEN_SPACE'],
                                           params['STUDY_AREA_GRID'],
                                           context, feedback)
        gridNeto = grid

        steps = steps+1
        feedback.setCurrentStep(steps)
        segmentsOpenSpace = intersection(params['OPEN_SPACE'], gridNeto['OUTPUT'],
                                [],
                                'id_grid;area_grid',
                                context, feedback)
        steps = steps+1
        feedback.setCurrentStep(steps)
        segmentsOpenSpaceArea = calculateArea(segmentsOpenSpace['OUTPUT'],
                                     'area_seg',
                                     context, feedback)


        steps = steps+1
        feedback.setCurrentStep(steps)
        segmentsOpenSpaceFixed = makeSureInside(segmentsOpenSpaceArea['OUTPUT'],
                                                 context,
                                                 feedback)
        steps = steps+1
        feedback.setCurrentStep(steps)
        gridNetoAndSegmentsOpenSpace = joinByLocation(gridNeto['OUTPUT'],
                                             segmentsOpenSpaceFixed['OUTPUT'],
                                             'area_seg;',                                  
                                              [CONTIENE], [SUM],
                                              UNDISCARD_NONMATCHING,
                                              context,
                                              feedback)  

        steps = steps+1
        feedback.setCurrentStep(steps)
        space2improvInGrid = intersection(params['SPACE2IMPROVEMENT'], gridNeto['OUTPUT'],
                                    [],
                                    [],
                                    context, feedback)    



        steps = steps+1
        feedback.setCurrentStep(steps)
        space2improvArea = calculateArea(space2improvInGrid['OUTPUT'],
                                'area_improv',
                                context, feedback)


        steps = steps+1
        feedback.setCurrentStep(steps)
        space2improvAreaFixed = makeSureInside(space2improvArea['OUTPUT'],
                                      context,
                                      feedback)    

        steps = steps+1
        feedback.setCurrentStep(steps)
        emptyProperties = joinByLocation(gridNetoAndSegmentsOpenSpace['OUTPUT'],
                                              space2improvAreaFixed['OUTPUT'],
                                              'area_improv',
                                              [CONTIENE], [SUM],
                                              UNDISCARD_NONMATCHING,                              
                                              context,
                                              feedback)

        steps = steps+1
        feedback.setCurrentStep(steps)
        formulaopenSpace2ImprovSurface = 'coalesce((area_improv_sum/area_seg_sum) * 100, 0)'
        openSpace2ImprovSurface = calculateField(emptyProperties['OUTPUT'],
                                    NAMES_INDEX['ID04'][0],
                                   formulaopenSpace2ImprovSurface,
                                   context,
                                   feedback, params['OUTPUT'])



        return openSpace2ImprovSurface


    def icon(self):
        return QIcon(os.path.join(pluginPath, 'sisurbano', 'icons', 'warninghouse.jpeg'))

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'D04 Espacios públicos abiertos que necesitan mejoras'

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
        return ID04OpenPublicSpacesNeedImprovement()

    def shortHelpString(self):
        return  "<b>Descripción:</b><br/>"\
                "<span>Mide el porcentaje de espacios públicos abiertos (parques, plazas, parques cívicos, parque infantil, campo deportivo, margen de agua, parque lineal, bulevards y mercados abiertos) que necesitan mejoras en cuanto a la estructura, mobiliario, vegetación en relación con el número total de espacios públicos.</span>"\
                "<br/><br/><b>Justificación y metodología:</b><br/>"\
                "<span>Se consideran los lotes de espacio público, en base al registro más reciente del estado actual. </span>"\
                "<br/><br/><b>Formula:</b><br/>"\
                "<span>(Superficie de espacios públicos abiertos que necesitan mejoras en m2 / Superficie total de espacios públicos abiertos en m2)*100<br/>"