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
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSink)
from .ZProcesses import *
from .Zettings import *
from .ZHelpers import *

pluginPath = os.path.split(os.path.split(os.path.dirname(__file__))[0])[0]

class IC04Proximity2AlternativeTransport(QgsProcessingAlgorithm):
    """
    Mide el porcentaje de población que tiene acceso simultáneo a tres
    o más redes de transporte alternativo (bus, tranvía, bici pública,
    ciclovías, caminos peatonales). Se considera que la población tiene
    acceso a una red de transporte si su vivienda se encuentra dentro
    del área de influencia de dicha red, según lo siguiente: a 300m de
    una parada de bus urbano, 500m de una parada de tranvía, 300m de
    una estación de bici pública, 300m de ciclovías, y 300m de caminos
    peatonales.
    Formula: (Población cubierta por al menos 3 redes de transporte alternativo / Población total)*100

    Proximidad se define como viviendas ubicadas a:

    300m o menos de una parada de bus urbano, 
    500m o menos de una parada de tranvía,
    300m o menos de una estacíon de bici pública, 
    300m o menos de una ciclovía, 
    300m o menos de caminos peatonales    
    """

    BLOCKS = 'BLOCKS'
    FIELD_POPULATE_HOUSING = 'FIELD_POPULATE_HOUSING'
    CELL_SIZE = 'CELL_SIZE'    
    BUSSTOP = 'BUSSTOP'    
    TRAMSTOP = 'TRAMSTOP'    
    BIKESTOP = 'BIKESTOP'    
    BIKEWAY = 'BIKEWAY'    
    CROSSWALK = 'CROSSWALK'    
    OUTPUT = 'OUTPUT'
    STUDY_AREA_GRID = 'STUDY_AREA_GRID'    

    DISTANCE_OPTIONS = 'DISTANCE_OPTIONS'
    ROADS = 'ROADS'    



    def initAlgorithm(self, config):
        currentPath = getCurrentPath(self)
        FULL_PATH = buildFullPathName(currentPath, nameWithOuputExtension(NAMES_INDEX['IC04'][1]))           
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
                self.tr('Viviendas'),
                'viviendas', 'BLOCKS'
            )
        )      


        self.addParameter(
          QgsProcessingParameterEnum(
          self.DISTANCE_OPTIONS,
          self.tr('Tipo de distancia'),
          options=['ISOCRONA','RADIAL'], 
          allowMultiple=False, 
          defaultValue=1)
        )            


        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.ROADS,
                self.tr('Red vial (obligatorio para distancia ISOCRONA)'),
                [QgsProcessing.TypeVectorLine],
                optional = True,
                defaultValue = ''
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
            QgsProcessingParameterFeatureSource(
                self.BUSSTOP,
                self.tr('Paradas de bus'),
                [QgsProcessing.TypeVectorPoint],
                optional = True
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.TRAMSTOP,
                self.tr('Tranvía'),
                [QgsProcessing.TypeVectorPoint],
                optional = True
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.BIKESTOP,
                self.tr('Bici pública'),
                [QgsProcessing.TypeVectorPoint],
                optional = True
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.BIKEWAY,
                self.tr('Ciclovía'),
                [QgsProcessing.TypeVectorLine],
                optional = True
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.CROSSWALK,
                self.tr('Caminos peatonales'),
                [QgsProcessing.TypeVectorLine],
                optional = True
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
      isValid = lambda x: 0 if x is None else 1
      isBusStop = isValid(params['BUSSTOP'])
      isTramStop = isValid(params['TRAMSTOP'])
      isBikeStop = isValid(params['BIKESTOP'])
      isBikeWay = isValid(params['BIKEWAY'])
      isCrossWalk = isValid(params['CROSSWALK'])
      isRoads = isValid(params['ROADS'])
      totalValides = isBusStop + isTramStop+ isBikeStop + isBikeWay + isCrossWalk

      if(totalValides >=3):
        if isRoads == 0 and params['DISTANCE_OPTIONS'] == 0:
          feedback.reportError(str(('Distancia isocrona requiere la red vial')))            
          return {}

        steps = 0
        totalStpes = 37
        fieldPopulateOrHousing = params['FIELD_POPULATE_HOUSING']
        DISTANCE_BUSSTOP = 300
        DISTANCE_TRAMSTOP = 500
        DISTANCE_BKESTOP = 300
        DISTANCE_BIKEWAY = 300
        DISTANCE_CROSSWALK = 300


        MIN_FACILITIES = 3
        OPERATOR_GE = 3

        feedback = QgsProcessingMultiStepFeedback(totalStpes, feedback)

        """
        -----------------------------------------------------------------
        Calcular las facilidades
        -----------------------------------------------------------------
        """

        steps = steps+1
        feedback.setCurrentStep(steps)
        if not OPTIONAL_GRID_INPUT: params['CELL_SIZE'] = P_CELL_SIZE
        grid, isStudyArea = buildStudyArea(params['CELL_SIZE'], params['BLOCKS'],
                                           params['STUDY_AREA_GRID'],
                                           context, feedback)
        gridNeto = grid  


        steps = steps+1
        feedback.setCurrentStep(steps)        
        blocks = calculateArea(params['BLOCKS'], 'area_bloc', context,
                               feedback)

        steps = steps+1
        feedback.setCurrentStep(steps)
        segments = intersection(blocks['OUTPUT'], gridNeto['OUTPUT'],
                                'area_bloc;' + fieldPopulateOrHousing,
                                'id_grid',
                                context, feedback)

        steps = steps+1
        feedback.setCurrentStep(steps)
        segmentsArea = calculateArea(segments['OUTPUT'],
                                     'area_seg',
                                     context, feedback)

        steps = steps+1
        feedback.setCurrentStep(steps)
        formulaPopulationSegments = '(area_seg/area_bloc) * ' + fieldPopulateOrHousing
        populationForSegments = calculateField(segmentsArea['OUTPUT'], 'pop_seg',
                                            formulaPopulationSegments,
                                            context,
                                            feedback)
        steps = steps+1
        feedback.setCurrentStep(steps)
        blocksWithId = calculateField(populationForSegments['OUTPUT'], 'id_block', '$id', context,
                                      feedback, type=1)

        steps = steps+1
        feedback.setCurrentStep(steps)
        centroidsBlocks = createCentroids(blocksWithId['OUTPUT'], context,
                                          feedback)

        result = []

        idxs = ['idxbus','idxtram','idxbikestop','idkbikeway','idxwalk']

        layers = []

        if(params['DISTANCE_OPTIONS'] == 0):
          steps = steps+1
          feedback.setCurrentStep(steps)        
          feedback.pushConsoleInfo(str(('Cálculo de áreas de servicio')))   

          pointsBikeWay = pointsAlongLines(params['BIKEWAY'], 50, context, feedback)  
          pointsCrossWalk = pointsAlongLines(params['CROSSWALK'], 50, context, feedback) 


          if isBusStop == 1: layers.append([params['BUSSTOP'], STRATEGY_DISTANCE, DISTANCE_BUSSTOP])
          if isTramStop == 1: layers.append([params['TRAMSTOP'], STRATEGY_DISTANCE, DISTANCE_TRAMSTOP])
          if isBikeStop == 1: layers.append([params['BIKESTOP'], STRATEGY_DISTANCE, DISTANCE_BKESTOP])
          if isBikeWay == 1:  layers.append([pointsBikeWay['OUTPUT'], STRATEGY_DISTANCE, DISTANCE_BIKEWAY])
          if isCrossWalk == 1:  layers.append([pointsCrossWalk['OUTPUT'], STRATEGY_DISTANCE, DISTANCE_CROSSWALK])

          serviceAreas = multiBufferIsocrono(params['ROADS'], layers, context, feedback)

          iidx = -1
          for serviceArea in serviceAreas:
            iidx = iidx + 1
            idx = idxs[iidx] 
            steps = steps+1
            feedback.setCurrentStep(steps)
            serviceArea = calculateField(serviceArea, idx, '$id', context,
                                          feedback, type=1)        
            steps = steps+1
            feedback.setCurrentStep(steps)
            centroidsBlocks = joinByLocation(centroidsBlocks['OUTPUT'],
                                      serviceArea['OUTPUT'],
                                      [idx], [INTERSECTA], [COUNT],
                                      UNDISCARD_NONMATCHING,
                                      context,
                                      feedback)        
     
          steps = steps+1
          feedback.setCurrentStep(steps)
          # formulaDummy = 'idxbus_count * 1'
          formulaDummy = 'coalesce(idxbus_count, 0) + coalesce(idxtram_count, 0) + coalesce(idxbikestop_count,0) + coalesce(idkbikeway_count, 0) + coalesce(idxwalk_count, 0)'
          facilitiesCover = calculateField(centroidsBlocks['OUTPUT'], 'facilities',
                                            formulaDummy,
                                            context,
                                            feedback)      

          steps = steps+1
          feedback.setCurrentStep(steps)
          facilitiesFullCover = filter(facilitiesCover['OUTPUT'],
                                                     'facilities', OPERATOR_GE,
                                                     MIN_FACILITIES, context, feedback)       


          steps = steps+1
          feedback.setCurrentStep(steps)
          gridNetoFacilitiesCover = joinByLocation(gridNeto['OUTPUT'],
                                               facilitiesCover['OUTPUT'],
                                               ['pop_seg','facilities'],
                                               [CONTIENE], [SUM], UNDISCARD_NONMATCHING,                 
                                               context,
                                               feedback)     

          fieldsMapping = [
              {'expression': '"id_grid"', 'length': 10, 'name': 'id_grid', 'precision': 0, 'type': 4}, 
              {'expression': '"area_grid"', 'length': 16, 'name': 'area_grid', 'precision': 3, 'type': 6}, 
              {'expression': '"pop_seg_sum"', 'length': 20, 'name': 'ptotal', 'precision': 2, 'type': 6},
              {'expression': '"facilities_sum"', 'length': 20, 'name': 'facilities', 'precision': 2, 'type': 6}
          ]      
          

          steps = steps+1
          feedback.setCurrentStep(steps)
          gridNetoFacilitiesCover = refactorFields(fieldsMapping, gridNetoFacilitiesCover['OUTPUT'], 
                                  context,
                                  feedback)             



          steps = steps+1
          feedback.setCurrentStep(steps)
          gridNetoFacilities = joinByLocation(gridNetoFacilitiesCover['OUTPUT'],
                                               facilitiesFullCover['OUTPUT'],
                                               ['pop_seg'],
                                               [CONTIENE], [SUM], UNDISCARD_NONMATCHING,                 
                                               context,
                                               feedback)

          steps = steps+1
          feedback.setCurrentStep(steps)
          formulaProximity = 'coalesce((coalesce(pop_seg_sum,0) / coalesce(ptotal,""))*100,"")'
          proximity2AlternativeTransport = calculateField(gridNetoFacilities['OUTPUT'], NAMES_INDEX['IC04'][0],
                                            formulaProximity,
                                            context,
                                            feedback, params['OUTPUT'])        

          result = proximity2AlternativeTransport                                                                                                                               
                
        else:
          feedback.pushConsoleInfo(str(('Cálculo de buffer radial')))
          blocksJoined = blocksWithId
          
          steps = steps+1
          feedback.setCurrentStep(steps)
          blockBuffer4BusStop = createBuffer(centroidsBlocks['OUTPUT'], DISTANCE_BUSSTOP,
                                               context,
                                               feedback)
          
          # ------------------------------------

          if isBusStop == 1:
            steps = steps+1
            feedback.setCurrentStep(steps)
            layerBusStop = calculateField(params['BUSSTOP'], 'idx', '$id', context,
                                          feedback, type=1)          

            layerBusStop = layerBusStop['OUTPUT']
            steps = steps+1
            feedback.setCurrentStep(steps)
            counterBusStop = joinByLocation(blockBuffer4BusStop['OUTPUT'],
                                              layerBusStop,
                                              'idx', [INTERSECTA], [COUNT],
                                              UNDISCARD_NONMATCHING,
                                              context,
                                              feedback)
            steps = steps+1
            feedback.setCurrentStep(steps)
            blocksJoined = joinByAttr(blocksJoined['OUTPUT'], 'id_block',
                                      counterBusStop['OUTPUT'], 'id_block',
                                      'idx_count',
                                      UNDISCARD_NONMATCHING,
                                      'bs_',
                                      context,
                                      feedback)


          # ---------------------------------------------------
          if isTramStop == 1:
            steps = steps+1
            feedback.setCurrentStep(steps)
            blockBuffer4TramStop = createBuffer(centroidsBlocks['OUTPUT'], DISTANCE_TRAMSTOP, context,
                                              feedback)


            steps = steps+1
            feedback.setCurrentStep(steps)
            layerTramStop = calculateField(params['TRAMSTOP'], 'idx', '$id', context,
                                          feedback, type=1)              

            layerTramStop = layerTramStop['OUTPUT']
            steps = steps+1
            feedback.setCurrentStep(steps)
            counterTramStop = joinByLocation(blockBuffer4TramStop['OUTPUT'],
                                           layerTramStop,
                                           'idx', [INTERSECTA], [COUNT],
                                           UNDISCARD_NONMATCHING,
                                           context,
                                           feedback)   

            steps = steps+1
            feedback.setCurrentStep(steps)
            blocksJoined = joinByAttr(blocksJoined['OUTPUT'], 'id_block',
                                      counterTramStop['OUTPUT'], 'id_block',
                                      'idx_count',
                                      UNDISCARD_NONMATCHING,
                                      'ts_',
                                      context,
                                      feedback)             

          # -----------------------------------------------  
          if isBikeStop == 1:                                              
            steps = steps+1
            feedback.setCurrentStep(steps)
            blockBuffer4BikeStop = createBuffer(centroidsBlocks['OUTPUT'], DISTANCE_BKESTOP, context,
                                               feedback)

            steps = steps+1
            feedback.setCurrentStep(steps)
            layerBikeStop = calculateField(params['BIKESTOP'], 'idx', '$id', context,
                                          feedback, type=1)      

            layerBikeStop = layerBikeStop['OUTPUT']
            steps = steps+1
            feedback.setCurrentStep(steps)
            counteBikeStop = joinByLocation(blockBuffer4BikeStop['OUTPUT'],
                                            layerBikeStop,
                                            'idx', [INTERSECTA], [COUNT],
                                            UNDISCARD_NONMATCHING,
                                            context,
                                            feedback)


            steps = steps+1
            feedback.setCurrentStep(steps)
            blocksJoined = joinByAttr(blocksJoined['OUTPUT'], 'id_block',
                                      counteBikeStop['OUTPUT'], 'id_block',
                                      'idx_count',
                                      UNDISCARD_NONMATCHING,
                                      'bks_',
                                      context,
                                      feedback)   


          # -----------------------------------------

          if isBikeWay == 1:
            steps = steps+1
            feedback.setCurrentStep(steps)
            BlockBuffer4BikeWay = createBuffer(centroidsBlocks['OUTPUT'], DISTANCE_BIKEWAY,
                                              context, feedback)

            pointsBikeWay = pointsAlongLines(params['BIKEWAY'], 50, context, feedback)                   

            steps = steps+1
            feedback.setCurrentStep(steps)
            layerBikeWay = calculateField(pointsBikeWay['OUTPUT'], 'idx', '$id', context,
                                          feedback, type=1)   

            layerBikeWay = layerBikeWay['OUTPUT']
            steps = steps+1
            feedback.setCurrentStep(steps)
            counterBikeWay = joinByLocation(BlockBuffer4BikeWay['OUTPUT'],
                                          layerBikeWay,
                                          'idx', [INTERSECTA], [COUNT],
                                          UNDISCARD_NONMATCHING,
                                          context,
                                          feedback)          

            steps = steps+1
            feedback.setCurrentStep(steps)
            blocksJoined = joinByAttr(blocksJoined['OUTPUT'], 'id_block',
                                      counterBikeWay['OUTPUT'], 'id_block',
                                      'idx_count',
                                      UNDISCARD_NONMATCHING,
                                      'bw_',
                                      context,
                                      feedback)

          # ------------------------------------------
          if isCrossWalk == 1:
            steps = steps+1
            feedback.setCurrentStep(steps)
            BlockBuffer4CrossWalk = createBuffer(centroidsBlocks['OUTPUT'], DISTANCE_CROSSWALK,
                                              context, feedback)  

            pointsCrossWalk = pointsAlongLines(params['CROSSWALK'], 50, context, feedback)              

            steps = steps+1
            feedback.setCurrentStep(steps)
            layerCrossWalk = calculateField(pointsCrossWalk['OUTPUT'], 'idx', '$id', context,
                                          feedback, type=1)      

            layerCrossWalk = layerCrossWalk['OUTPUT']
            steps = steps+1
            feedback.setCurrentStep(steps)
            counterCrossWalk = joinByLocation(BlockBuffer4CrossWalk['OUTPUT'],
                                          layerCrossWalk,
                                          'idx', [INTERSECTA], [COUNT],
                                          UNDISCARD_NONMATCHING,
                                          context,
                                          feedback)  


            steps = steps+1
            feedback.setCurrentStep(steps)
            blocksJoined = joinByAttr(blocksJoined['OUTPUT'], 'id_block',
                                      counterCrossWalk['OUTPUT'], 'id_block',
                                      'idx_count',
                                      UNDISCARD_NONMATCHING,
                                      'cw_',
                                      context,
                                      feedback)              
          # --------------------------------------------                                                                                     
                        
       
          #TODO: CAMBIAR POR UN METODO BUCLE

          formulaParseBS = 'CASE WHEN coalesce(bs_idx_count, 0) > 0 THEN 1 ELSE 0 END'
          steps = steps+1
          feedback.setCurrentStep(steps)
          blocksFacilities = calculateField(blocksJoined['OUTPUT'], 'parse_bs',
                                            formulaParseBS,
                                            context,
                                            feedback)

          formulaParseTS = 'CASE WHEN coalesce(ts_idx_count, 0) > 0 THEN 1 ELSE 0 END'
          steps = steps+1
          feedback.setCurrentStep(steps)
          blocksFacilities = calculateField(blocksFacilities['OUTPUT'], 'parse_ts',
                                            formulaParseTS,
                                            context,
                                            feedback)    

          formulaParseBKS = 'CASE WHEN coalesce(bks_idx_count, 0) > 0 THEN 1 ELSE 0 END'
          steps = steps+1
          feedback.setCurrentStep(steps)
          blocksFacilities = calculateField(blocksFacilities['OUTPUT'], 'parse_bks',
                                            formulaParseBKS,
                                            context,
                                            feedback)    


          formulaParseBW = 'CASE WHEN coalesce(bw_idx_count, 0) > 0 THEN 1 ELSE 0 END'
          steps = steps+1
          feedback.setCurrentStep(steps)
          blocksFacilities = calculateField(blocksFacilities['OUTPUT'], 'parse_bw',
                                            formulaParseBW,
                                            context,
                                            feedback)  


          formulaParseCW = 'CASE WHEN coalesce(cw_idx_count, 0) > 0 THEN 1 ELSE 0 END'
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

          # Haciendo el buffer inverso aseguramos que los segmentos
          # quden dentro de la malla
          steps = steps+1
          feedback.setCurrentStep(steps)
          facilitiesForSegmentsFixed = makeSureInside(blocksFacilities['OUTPUT'],
                                                      context,
                                                      feedback)

          steps = steps+1
          feedback.setCurrentStep(steps)
          gridNetoAndSegments = joinByLocation(gridNeto['OUTPUT'],
                                               facilitiesForSegmentsFixed['OUTPUT'],
                                               'bs_idx_count;ts_idx_count;bks_idx_count;bw_idx_count;cw_idx_count;facilities;pop_seg',
                                               [CONTIENE], [MAX, SUM], UNDISCARD_NONMATCHING,                 
                                               context,
                                               feedback)

          # tomar solo los que tienen cercania simultanea (descartar lo menores de 3)
          steps = steps+1
          feedback.setCurrentStep(steps)
          facilitiesNotNullForSegmentsFixed = filter(facilitiesForSegmentsFixed['OUTPUT'],
                                                     'facilities', OPERATOR_GE,
                                                     MIN_FACILITIES, context, feedback)

          steps = steps+1
          feedback.setCurrentStep(steps)
          gridNetoAndSegmentsSimulta = joinByLocation(gridNeto['OUTPUT'],
                                                      facilitiesNotNullForSegmentsFixed['OUTPUT'],
                                                      'pop_seg',
                                                      [CONTIENE], [MAX, SUM], UNDISCARD_NONMATCHING,               
                                                      context,
                                                      feedback)

          steps = steps+1
          feedback.setCurrentStep(steps)
          totalHousing = joinByAttr(gridNetoAndSegments['OUTPUT'], 'id_grid',
                                    gridNetoAndSegmentsSimulta['OUTPUT'], 'id_grid',
                                    'pop_seg_sum',
                                    UNDISCARD_NONMATCHING,
                                    'net_',
                                    context,
                                    feedback)

          steps = steps+1
          feedback.setCurrentStep(steps)
          formulaProximity = 'coalesce((coalesce(net_pop_seg_sum,0) /  coalesce(pop_seg_sum,""))*100,"")'
          proximity2AlternativeTransport = calculateField(totalHousing['OUTPUT'], NAMES_INDEX['IC04'][0],
                                            formulaProximity,
                                            context,
                                            feedback, params['OUTPUT'])

          result = proximity2AlternativeTransport

        return result
      else:
         feedback.reportError(str(('Se necesita al menos tres redes de transporte')))    

         return {}


        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        #return {self.OUTPUT: dest_id}

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'sisurbano', 'icons', 'tram.png'))

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'C04 Proximidad a redes de transporte alternativo'

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
        return 'C Movilidad urbana'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return IC04Proximity2AlternativeTransport()

    def shortHelpString(self):
        return  "<b>Descripción:</b><br/>"\
                "<span>Mide el porcentaje de población que tiene acceso simultáneo a tres o más redes de transporte alternativo (bus, tranvía, bici pública, ciclovías y senderos peatonales). Se considera que la población tiene acceso a una red de transporte si su vivienda se encuentra dentro del área de influencia de dicha red, según lo siguiente: a 300m de una parada de bus urbano, 500m de una parada de tranvía, 300m de una estación de bici pública, 300m de ciclovías, y 300m de un sendero peatonal.</span>"\
                "<br/><br/><b>Justificación y metodología:</b><br/>"\
                "<span>Proximidad se define como viviendas ubicadas a: 300m o menos de una parada de bus urbano, 500m o menos de una parada de tranvía, 300m o menos de una estación de bici pública, 300m o menos de una ciclovía, 300m o menos de senderos peatonales</span>"\
                "<br/><br/><b>Formula:</b><br/>"\
                "<span>(Población cubierta por al menos 3 redes de transporte alternativo / Población total)*100<br/>"         

