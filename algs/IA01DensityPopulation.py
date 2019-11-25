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

class IA01DensityPopulation(QgsProcessingAlgorithm):
    """
    Mide la concentración de habitantes y evidencia indirectamente la demanda
    de movilidad, productos y servicios. Número de habitantes por la
    superficie de suelo de naturaleza urbana (no incluye vías
    y equipamientos).
    Formula: Número de habitantes / Superficie efectiva neta en hectareas
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    BLOCKS = 'BLOCKS'
    FIELD_POPULATION = 'FIELD_POPULATION'
    CELL_SIZE = 'CELL_SIZE'
    OUTPUT = 'OUTPUT'
    STUDY_AREA_GRID = 'STUDY_AREA_GRID'


    def initAlgorithm(self, config):

        currentPath = getCurrentPath(self)
        FULL_PATH = buildFullPathName(currentPath, nameWithOuputExtension(NAMES_INDEX['IA01'][1]))

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.BLOCKS,
                self.tr('Manzanas'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_POPULATION,
                self.tr('Población'),
                'poblacion', 'BLOCKS'
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
        totalStpes = 11
        fieldPopulation = params['FIELD_POPULATION']

        feedback = QgsProcessingMultiStepFeedback(totalStpes, feedback)

        blocks = calculateArea(params['BLOCKS'], 'area_bloc', context,
                               feedback)


        steps = steps+1
        feedback.setCurrentStep(steps)
        if not OPTIONAL_GRID_INPUT: params['CELL_SIZE'] = P_CELL_SIZE
        grid, isStudyArea = buildStudyArea(params['CELL_SIZE'], params['BLOCKS'],
                                           params['STUDY_AREA_GRID'],
                                           context, feedback)
        gridNeto = grid



        steps = steps+1
        feedback.setCurrentStep(steps)
        segments = intersection(blocks['OUTPUT'], gridNeto['OUTPUT'],
                                'area_bloc;' + fieldPopulation,
                                'id_grid;area_grid',
                                context, feedback)

        steps = steps+1
        feedback.setCurrentStep(steps)
        segmentsArea = calculateArea(segments['OUTPUT'],
                                     'area_seg',
                                     context, feedback)

        steps = steps+1
        feedback.setCurrentStep(steps)
        formulaPopulationSegments = '(area_seg/area_bloc) * ' + fieldPopulation
        populationForSegments = calculateField(segmentsArea['OUTPUT'], 'pop_seg',
                                               formulaPopulationSegments,
                                               context,
                                               feedback)

        # Haciendo el buffer inverso aseguramos que los segmentos
        # quden dentro de la malla
        steps = steps+1
        feedback.setCurrentStep(steps)
        populationForSegmentsFixed = makeSureInside(populationForSegments['OUTPUT'],
                                                    context,
                                                    feedback)

        steps = steps+1
        feedback.setCurrentStep(steps)

     
        gridNetoAndSegments = joinByLocation(gridNeto['OUTPUT'],
                                             populationForSegmentsFixed['OUTPUT'],
                                             'area_seg;pop_seg',                                   
                                              [CONTIENE], [SUM],
                                              UNDISCARD_NONMATCHING,
                                              context,
                                              feedback)   


        steps = steps+1
        feedback.setCurrentStep(steps)
        formulaNetDensityPopulationPerHa = 'coalesce((pop_seg_sum/area_seg_sum)*10000, 0)'
        densities = calculateField(gridNetoAndSegments['OUTPUT'],
                                   NAMES_INDEX['IA01'][0],
                                   formulaNetDensityPopulationPerHa,
                                   context,
                                   feedback)


        steps = steps+1
        feedback.setCurrentStep(steps)
        formulaGrossDensityPopulationPerHa = 'coalesce((pop_seg_sum/area_grid)*10000, 0)'
        densities = calculateField(densities['OUTPUT'],
                                   'i_gdp',
                                   formulaGrossDensityPopulationPerHa,
                                   context,
                                   feedback, params['OUTPUT'])



        return densities

        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        #return {self.OUTPUT: dest_id}

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'sisurbano', 'icons', 'population.png'))

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'A01 Densidad neta de habitantes'

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
        return IA01DensityPopulation()

    def shortHelpString(self):
        return  "<b>Descripción:</b><br>"\
                "<span>Mide la concentración de habitantes y evidencia indirectamente la demanda</span><br>"\
                "<span>de movilidad, productos y servicios. Número de habitantes por la</span><br>"\
                "<span>superficie de suelo de naturaleza urbana (no incluye vías y equipamientos).</span><br>"\
                "<b>Formula:</b><br>"\
                "<span>Número de habitantes / Superficie efectiva neta en hectareas</span><br>"\