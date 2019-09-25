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

class IA09CoverageDailyBusinessActivities(QgsProcessingAlgorithm):
    """
    Mide la cobertura simultánea de actividades comerciales cotidianas
    (tienda de abarrotes, minimercado, farmacia, panadería, papelería-bazar),
    poniendo de manifiesto la actividad de la calle y el tiempo invertido en
    desplazamientos relacionados con estas tareas. Relación entre la superficie
    de suelo que simultaneamente se encuentra dentro del radio de cobertura de
    300m de cada una de estas actividades comerciales cotidianas y el área bruta
    del área estudio.
    
    Áreas cubiertas se consideran aquellas que simultáneamente quedan cubiertas
    al trazar un radio de 300m desde cada tipo de actividad comercial cotidiana.
    Actividades comerciales cotidianas se consideran: tienda de abarrotes, minimercado,
    farmacia, panadería, papelería-bazar.

    Formula: (Área con cobertura simultánea Act.Cot. / Área total)*100
    """

    BLOCKS = 'BLOCKS'
    FIELD_POPULATE_HOUSING = 'FIELD_POPULATE_HOUSING'
    CELL_SIZE = 'CELL_SIZE'    
    SHOP = 'SHOP'    
    MINIMARKET = 'MINIMARKET'    
    PHARMACY = 'PHARMACY'    
    BAKERY = 'BAKERY'    
    STATIONERY = 'STATIONERY'    
    OUTPUT = 'OUTPUT'



    def initAlgorithm(self, config):
        currentPath = getCurrentPath(self)
        FULL_PATH = buildFullPathName(currentPath, nameWithOuputExtension(NAMES_INDEX['IA09'][1]))           
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.BLOCKS,
                self.tr('Manzanas'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_POPULATE_HOUSING,
                self.tr('Población o viviendas'),
                'poblacion', 'BLOCKS'
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
                self.SHOP,
                self.tr('Tiendas de abarrotes'),
                [QgsProcessing.TypeVectorAnyGeometry],
                '', True
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.MINIMARKET,
                self.tr('Minimercados'),
                [QgsProcessing.TypeVectorAnyGeometry],
                '', True
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.PHARMACY,
                self.tr('Farmacias'),
                [QgsProcessing.TypeVectorAnyGeometry],
                '', True
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.BAKERY,
                self.tr('Panaderías'),
                [QgsProcessing.TypeVectorAnyGeometry],
                '', True
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.STATIONERY,
                self.tr('Papelerías-bazar'),
                [QgsProcessing.TypeVectorAnyGeometry],
                '', True
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
      totalStpes = 37
      fieldPopulateOrHousing = params['FIELD_POPULATE_HOUSING']
      DISTANCE_SHOP = 300
      DISTANCE_MINIMARKET =300
      DISTANCE_PHARMACY = 300
      DISTANCE_BAKERY = 300
      DISTANCE_STATIONERY = 300


      feedback = QgsProcessingMultiStepFeedback(totalStpes, feedback)

      """
      -----------------------------------------------------------------
      Calcular las facilidades
      -----------------------------------------------------------------
      """

      steps = steps+1
      feedback.setCurrentStep(steps)
      blocksWithId = calculateField(params['BLOCKS'], 'id_block', '$id', context,
                                    feedback, type=1)

      steps = steps+1
      feedback.setCurrentStep(steps)
      centroidsBlocks = createCentroids(blocksWithId['OUTPUT'], context,
                                        feedback)

      steps = steps+1
      feedback.setCurrentStep(steps)
      blockBuffer4Shop = createBuffer(centroidsBlocks['OUTPUT'], DISTANCE_SHOP,
                                           context,
                                           feedback)

      steps = steps+1
      feedback.setCurrentStep(steps)
      blockBuffer4Minimarket = createBuffer(centroidsBlocks['OUTPUT'], DISTANCE_MINIMARKET, context,
                                        feedback)

      steps = steps+1
      feedback.setCurrentStep(steps)
      blockBuffer4Pharmacy = createBuffer(centroidsBlocks['OUTPUT'], DISTANCE_PHARMACY, context,
                                         feedback)

      steps = steps+1
      feedback.setCurrentStep(steps)
      BlockBuffer4Bakery = createBuffer(centroidsBlocks['OUTPUT'], DISTANCE_BAKERY,
                                        context, feedback)

      steps = steps+1
      feedback.setCurrentStep(steps)
      BlockBuffer4Stationery = createBuffer(centroidsBlocks['OUTPUT'], DISTANCE_STATIONERY,
                                        context, feedback)    



      steps = steps+1
      feedback.setCurrentStep(steps)
      layerShop = calculateField(params['SHOP'], 'idx', '$id', context,
                                    feedback, type=1)


      steps = steps+1
      feedback.setCurrentStep(steps)
      layerMinimarket = calculateField(params['MINIMARKET'], 'idx', '$id', context,
                                    feedback, type=1)    

      steps = steps+1
      feedback.setCurrentStep(steps)
      layerPharmacy = calculateField(params['PHARMACY'], 'idx', '$id', context,
                                    feedback, type=1)       


      steps = steps+1
      feedback.setCurrentStep(steps)
      layerBakery = calculateField(params['BAKERY'], 'idx', '$id', context,
                                    feedback, type=1)   


      steps = steps+1
      feedback.setCurrentStep(steps)
      layerStationery = calculateField(params['STATIONERY'], 'idx', '$id', context,
                                    feedback, type=1)                                        


      layerShop = layerShop['OUTPUT']
      layerMinimarket = layerMinimarket['OUTPUT']
      layerPharmacy = layerPharmacy['OUTPUT']
      layerBakery = layerBakery['OUTPUT']
      layerStationery = layerStationery['OUTPUT']


      steps = steps+1
      feedback.setCurrentStep(steps)
      counterShop = joinByLocation(blockBuffer4Shop['OUTPUT'],
                                        layerShop,
                                        'idx', [INTERSECTA], [COUNT],
                                        UNDISCARD_NONMATCHING,
                                        context,
                                        feedback)
      steps = steps+1
      feedback.setCurrentStep(steps)
      counterMinimarket = joinByLocation(blockBuffer4Minimarket['OUTPUT'],
                                     layerMinimarket,
                                     'idx', [INTERSECTA], [COUNT],
                                     UNDISCARD_NONMATCHING,
                                     context,
                                     feedback)
      steps = steps+1
      feedback.setCurrentStep(steps)
      countePharmacy = joinByLocation(blockBuffer4Pharmacy['OUTPUT'],
                                      layerPharmacy,
                                      'idx', [INTERSECTA], [COUNT],
                                      UNDISCARD_NONMATCHING,
                                      context,
                                      feedback)
      steps = steps+1
      feedback.setCurrentStep(steps)
      counterBakery = joinByLocation(BlockBuffer4Bakery['OUTPUT'],
                                    layerBakery,
                                    'idx', [INTERSECTA], [COUNT],
                                    UNDISCARD_NONMATCHING,
                                    context,
                                    feedback)

      steps = steps+1
      feedback.setCurrentStep(steps)
      counterStationery = joinByLocation(BlockBuffer4Stationery['OUTPUT'],
                                    layerStationery,
                                    'idx', [INTERSECTA], [COUNT],
                                    UNDISCARD_NONMATCHING,
                                    context,
                                    feedback)    

      steps = steps+1
      feedback.setCurrentStep(steps)
      blocksJoined = joinByAttr(blocksWithId['OUTPUT'], 'id_block',
                                counterShop['OUTPUT'], 'id_block',
                                'idx_count',
                                UNDISCARD_NONMATCHING,
                                'sh_',
                                context,
                                feedback)

      steps = steps+1
      feedback.setCurrentStep(steps)
      blocksJoined = joinByAttr(blocksJoined['OUTPUT'], 'id_block',
                                counterMinimarket['OUTPUT'], 'id_block',
                                'idx_count',
                                UNDISCARD_NONMATCHING,
                                'mk_',
                                context,
                                feedback)

      steps = steps+1
      feedback.setCurrentStep(steps)
      blocksJoined = joinByAttr(blocksJoined['OUTPUT'], 'id_block',
                                countePharmacy['OUTPUT'], 'id_block',
                                'idx_count',
                                UNDISCARD_NONMATCHING,
                                'pha_',
                                context,
                                feedback)

      steps = steps+1
      feedback.setCurrentStep(steps)
      blocksJoined = joinByAttr(blocksJoined['OUTPUT'], 'id_block',
                                counterBakery['OUTPUT'], 'id_block',
                                'idx_count',
                                UNDISCARD_NONMATCHING,
                                'bk_',
                                context,
                                feedback)


      steps = steps+1
      feedback.setCurrentStep(steps)
      blocksJoined = joinByAttr(blocksJoined['OUTPUT'], 'id_block',
                                counterStationery['OUTPUT'], 'id_block',
                                'idx_count',
                                UNDISCARD_NONMATCHING,
                                'st_',
                                context,
                                feedback)    





      #FIXME: CAMBIAR POR UN METODO BUCLE

      formulaParseBS = 'CASE WHEN coalesce(sh_idx_count, 0) > 0 THEN 1 ELSE 0 END'
      formulaParseTS = 'CASE WHEN coalesce(mk_idx_count, 0) > 0 THEN 1 ELSE 0 END'
      formulaParseBKS = 'CASE WHEN coalesce(pha_idx_count, 0) > 0 THEN 1 ELSE 0 END'
      formulaParseBW = 'CASE WHEN coalesce(bk_idx_count, 0) > 0 THEN 1 ELSE 0 END'
      formulaParseCW = 'CASE WHEN coalesce(st_idx_count, 0) > 0 THEN 1 ELSE 0 END'


      steps = steps+1
      feedback.setCurrentStep(steps)
      blocksFacilities = calculateField(blocksJoined['OUTPUT'], 'parse_bs',
                                        formulaParseBS,
                                        context,
                                        feedback)

      steps = steps+1
      feedback.setCurrentStep(steps)
      blocksFacilities = calculateField(blocksFacilities['OUTPUT'], 'parse_ts',
                                        formulaParseTS,
                                        context,
                                        feedback)    


      steps = steps+1
      feedback.setCurrentStep(steps)
      blocksFacilities = calculateField(blocksFacilities['OUTPUT'], 'parse_bks',
                                        formulaParseBKS,
                                        context,
                                        feedback)    


      steps = steps+1
      feedback.setCurrentStep(steps)
      blocksFacilities = calculateField(blocksFacilities['OUTPUT'], 'parse_bw',
                                        formulaParseBW,
                                        context,
                                        feedback)  


      steps = steps+1
      feedback.setCurrentStep(steps)
      blocksFacilities = calculateField(blocksFacilities['OUTPUT'], 'parse_cw',
                                        formulaParseCW,
                                        context,
                                        feedback)  


      formulaFacilities = 'parse_bs + parse_ts + parse_bks + parse_bw + parse_cw'


      steps = steps+1
      feedback.setCurrentStep(steps)
      blocksFacilities = calculateField(blocksFacilities['OUTPUT'], 'facilities',
                                        formulaFacilities,
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
      segments = intersection(blocksFacilities['OUTPUT'], gridNeto['OUTPUT'],
                              'sh_idx_count;mk_idx_count;pha_idx_count;bk_idx_count;st_idx_count;facilities;' + fieldPopulateOrHousing,
                              'id_grid',
                              context, feedback)

      # Haciendo el buffer inverso aseguramos que los segmentos
      # quden dentro de la malla
      steps = steps+1
      feedback.setCurrentStep(steps)
      facilitiesForSegmentsFixed = makeSureInside(segments['OUTPUT'],
                                                  context,
                                                  feedback)

      steps = steps+1
      feedback.setCurrentStep(steps)
      gridNetoAndSegments = joinByLocation(gridNeto['OUTPUT'],
                                           facilitiesForSegmentsFixed['OUTPUT'],
                                           'sh_idx_count;mk_idx_count;pha_idx_count;bk_idx_count;st_idx_count;facilities;' + fieldPopulateOrHousing,
                                           [CONTIENE], [MAX, SUM], DISCARD_NONMATCHING,                 
                                           context,
                                           feedback)

      # tomar solo los que tienen cercania simultanea (descartar lo menores de 3)
      MIN_FACILITIES = 3
      OPERATOR_GE = 3
      steps = steps+1
      feedback.setCurrentStep(steps)
      facilitiesNotNullForSegmentsFixed = filter(facilitiesForSegmentsFixed['OUTPUT'],
                                                 'facilities', OPERATOR_GE,
                                                 MIN_FACILITIES, context, feedback)

      steps = steps+1
      feedback.setCurrentStep(steps)
      gridNetoAndSegmentsSimulta = joinByLocation(gridNeto['OUTPUT'],
                                                  facilitiesNotNullForSegmentsFixed['OUTPUT'],
                                                  fieldPopulateOrHousing,
                                                  [CONTIENE], [MAX, SUM], UNDISCARD_NONMATCHING,               
                                                  context,
                                                  feedback)

      steps = steps+1
      feedback.setCurrentStep(steps)
      totalHousing = joinByAttr(gridNetoAndSegments['OUTPUT'], 'id_grid',
                                gridNetoAndSegmentsSimulta['OUTPUT'], 'id_grid',
                                fieldPopulateOrHousing+'_sum',
                                DISCARD_NONMATCHING,
                                'net_',
                                context,
                                feedback)

      steps = steps+1
      feedback.setCurrentStep(steps)
      formulaProximity = '(coalesce(net_'+fieldPopulateOrHousing+'_sum,0) /  coalesce('+fieldPopulateOrHousing+'_sum,0))*100'
      proximity2AlternativeTransport = calculateField(totalHousing['OUTPUT'], NAMES_INDEX['IA09'][0],
                                        formulaProximity,
                                        context,
                                        feedback, params['OUTPUT'])

      return proximity2AlternativeTransport




        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        #return {self.OUTPUT: dest_id}

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'sisurbano', 'icons', 'green3.jpeg'))

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'A09 Cobertura de actividades comerciales cotinianas'

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
        return IA09CoverageDailyBusinessActivities()

