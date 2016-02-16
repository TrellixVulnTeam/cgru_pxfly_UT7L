# -*- coding: utf-8 -*-
import copy
import os
import time
import logging

import pymel.core as pm
import maya.cmds as cmds
import maya.mel as mel
from functools import partial

# make ui to pyQt style
set_QtStyle = 1  # 1 or 0

# Try import pySide module
try:
	from maya.OpenMayaUI import MQtUtil
	from shiboken import wrapInstance
	import PySide.QtGui as QtGui
	import PySide.QtCore as QtCore
	print 'dpaf_Afanasy: pySide can work.'
except:
	set_QtStyle = 0


logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)


class UI(object):
	"""The render UI
	"""

	def __init__(self):

		window = 'cgru_afanasy_wnd'

		if cmds.window(window, ex= 1):
			cmds.deleteUI(window)

		cmds.window(window, t= 'dpaf_Afanasy', s= 0, mxb= 0, mnb= 0, ret= 1)

		global dpaf_keepRendererNameDisplayCorrectly
		global dpaf_unRenderableLayers
		dpaf_keepRendererNameDisplayCorrectly = 0
		dpaf_unRenderableLayers = []

		#''' scriptJob here '''
		cmds.scriptJob(ac= ['defaultRenderGlobals.currentRenderer', partial(self.dpaf_setRendererName, 'current')], p= window)
		cmds.scriptJob(ac= ['defaultResolution.width', self.dpaf_changeResolution], p= window)
		cmds.scriptJob(ac= ['defaultResolution.height', self.dpaf_changeResolution], p= window)
		cmds.scriptJob(ac= ['defaultRenderGlobals.startFrame', partial(self.dpaf_getAttrSync, 'defaultRenderGlobals.startFrame', 'af_strFrm')], p= window)
		cmds.scriptJob(ac= ['defaultRenderGlobals.endFrame', partial(self.dpaf_getAttrSync, 'defaultRenderGlobals.endFrame', 'af_endFrm')], p= window)
		cmds.scriptJob(ac= ['defaultRenderGlobals.byFrameStep', partial(self.dpaf_getAttrSync, 'defaultRenderGlobals.byFrameStep', 'af_stpFrm')], p= window)
		cmds.scriptJob(con= ['defaultRenderGlobals.startFrame', partial(self.dpaf_getAttrSync, 'defaultRenderGlobals.startFrame', 'af_strFrm')], p= window)
		cmds.scriptJob(con= ['defaultRenderGlobals.endFrame', partial(self.dpaf_getAttrSync, 'defaultRenderGlobals.endFrame', 'af_endFrm')], p= window)
		cmds.scriptJob(con= ['defaultRenderGlobals.byFrameStep', partial(self.dpaf_getAttrSync, 'defaultRenderGlobals.byFrameStep', 'af_stpFrm')], p= window)
		cmds.scriptJob(e= ['timeUnitChanged', self.dpaf_rangeCtrlGetLayerAttr], p= window)
		cmds.scriptJob(e= ['renderLayerManagerChange', self.dpaf_layerMenuSync], p= window)
		cmds.scriptJob(e= ['renderLayerChange', self.dpaf_refreshLayerMenu], p= window)
		cmds.scriptJob(ac= ['defaultRenderLayer.renderable', partial(self.dpaf_layerRenderableTracker, 'defaultRenderLayer')], p= window)

		#''' UI frame '''
		cmds.columnLayout(adj= 1)
		cmds.frameLayout('afanasy_Frame', l= '', bgc= [0.31, 0.45, 0.20], li= 0, bs= 'out', w= 192, h = 246 + 184)
		cmds.formLayout('afanasy_Form')
		# separate layer
		cmds.checkBox('af_separate', l= 'Separate Layers', v= pm.optionVar.get('af_separate_layer_ov', 1), cc= self.dpaf_separateLayerAdj)
		# layer menu
		cmds.optionMenu('af_layerMenu', l= '', w= 157, ann= 'Layer menu, won\'t change current render layer.', cc= self.dpaf_rangeCtrlGetLayerAttr)
		# layer menu refresh button
		cmds.button('af_refresBtn', l= '', w= 6, h= 6, bgc= [.2, .3, .2], ann= 'Refresh layer optionMenu when error occurred.', c= self.dpaf_refreshLayerMenu_warning)
		# frame range
		cmds.text('af_strFrmTxt', l= 'S', fn= 'tinyBoldLabelFont')
		cmds.text('af_endFrmTxt', l= 'E', fn= 'tinyBoldLabelFont')
		cmds.text('af_stpFrmTxt', l= 'B', fn= 'tinyBoldLabelFont')
		cmds.floatField('af_strFrmFfd', w= 80, pre= 3, ann= 'Start frame.', cc= partial(self.dpaf_setAttrSync, 'defaultRenderGlobals.startFrame', 'af_strFrm'))
		cmds.popupMenu('af_startFrame_popupMenu', p= 'af_strFrmFfd', pmc= partial(self.dpaf_frameRangePopupMenuPostCmd, 'defaultRenderGlobals.startFrame', 'af_strFrmTxt'))
		cmds.floatField('af_endFrmFfd', w= 80, pre= 3, ann= 'End frame.', cc= partial(self.dpaf_setAttrSync, 'defaultRenderGlobals.endFrame', 'af_endFrm'))
		cmds.popupMenu('af_endFrame_popupMenu', p= 'af_endFrmFfd', pmc= partial(self.dpaf_frameRangePopupMenuPostCmd, 'defaultRenderGlobals.endFrame', 'af_endFrmTxt'))
		cmds.floatField('af_stpFrmFfd', w= 80, pre= 3, ann= 'By frame.', cc= partial(self.dpaf_setAttrSync, 'defaultRenderGlobals.byFrameStep', 'af_stpFrm'))
		cmds.popupMenu('af_byFrameStep_popupMenu', p= 'af_stpFrmFfd', pmc= partial(self.dpaf_frameRangePopupMenuPostCmd, 'defaultRenderGlobals.byFrameStep', 'af_stpFrmTxt'))
		# time line btn
		cmds.button('af_strAniBtn', l= 'Anim', bgc= [.21, .21, .21], w= 32, h= 18, c= partial(self.dpaf_setTimeLineRange, 'defaultRenderGlobals.startFrame', 'af_strFrm', 'ast'),
			ann= 'Use minimum animation range')
		cmds.button('af_strPbkBtn', l= 'PyBk', bgc= [.27, .27, .27], w= 32, h= 18, c= partial(self.dpaf_setTimeLineRange, 'defaultRenderGlobals.startFrame', 'af_strFrm', 'min'),
			ann= 'Use minimum playback range')
		cmds.button('af_endAniBtn', l= 'Anim', bgc= [.21, .21, .21], w= 32, h= 18, c= partial(self.dpaf_setTimeLineRange, 'defaultRenderGlobals.endFrame', 'af_endFrm', 'aet'),
			ann= 'Use maximum animation range')
		cmds.button('af_endPbkBtn', l= 'PyBk', bgc= [.27, .27, .27], w= 32, h= 18, c= partial(self.dpaf_setTimeLineRange, 'defaultRenderGlobals.endFrame', 'af_endFrm', 'max'),
			ann= 'Use maximum playback range')
		# image resolution
		mel.eval('setTestResolutionVar(1)')
		cmds.text('af_ResTextB', l= '', h= 9, w= 164, bgc= [0.1, 0.1, 0.1])
		vraySet = 0
		if cmds.objExists('vraySettings'):
			if cmds.attributeQuery('width', node= 'vraySettings', ex= 1): vraySet = 1
		cmds.text('af_ResTextW', l= str(cmds.getAttr('vraySettings.width' if vraySet else 'defaultResolution.width')), fn= 'smallPlainLabelFont')
		cmds.text('af_ResTextX', l= ' x ', fn= 'smallPlainLabelFont')
		cmds.text('af_ResTextH', l= str(cmds.getAttr('vraySettings.height' if vraySet else 'defaultResolution.height')), fn= 'smallPlainLabelFont')
		# render camera list
		cmds.text('af_cameraTxt', l= 'Render Camera list', fn= 'smallPlainLabelFont')
		cmds.textScrollList('af_cameraScr', w= 147, h= 57, fn= 'smallFixedWidthFont', dcc= 'print "camrea look"')
		cmds.iconTextButton('af_overriBtn', w= 20, h= 20, image= 'overrideSettings_dim.png', ann= 'Set override or remove override.',
										 c= 'cmds.iconTextButton("af_overriBtn", e= 1, ' +
											'image= "overrideSettings" + ("" if "_dim" in cmds.iconTextButton("af_overriBtn", q= 1, image= 1) ' +
											'and cmds.optionMenu("af_layerMenu", q= 1, v= 1) != "masterLayer" else "_dim") + ".png")')
		cmds.popupMenu('af_removeOverride_popupMenu', p= 'af_overriBtn', pmc= ('if cmds.optionMenu("af_layerMenu", q= 1, v= 1) == "masterLayer":\n' +
																		'	cmds.menuItem("af_removeOverride_item", e= 1, en= 0)\n' +
																		'else:\n' +
																		'	cmds.menuItem("af_removeOverride_item", e= 1, en= 1)'))
		cmds.menuItem('af_removeAllOverride_item', l= 'Remove all override', c= partial(self.dpaf_removeCamOverride, 1))
		cmds.menuItem('af_removeOverride_item', l= 'Remove override', c= partial(self.dpaf_removeCamOverride, 0))
		cmds.iconTextButton('af_addCamBtn', w= 20, h= 20, image= 'openAttribute.png', ann= 'List not renderable camera. Press green button to set selected renderable.'
			, c= self.dpaf_disrenderableCameraList)
		cmds.iconTextButton('af_delCamBtn', w= 20, h= 20, image= 'closeAttribute.png', ann= 'Remove renderable camera from list.'
			, c= partial(self.dpaf_adjRenderCamera, 0))
		# frame per tesk
		cmds.text('af_frmPTask_T', l= 'Frame Per Task', fn= 'smallPlainLabelFont')
		cmds.intField('af_frmPTask_F', w= 60, v= pm.optionVar.get('af_frmPTask_F_ov', 1))
		cmds.iconTextButton('af_frmPTask_B', w= 20, h= 20, image= 'removeRenderable.png', ann= 'set to default.'
			, c= partial(self.dpaf_setDefaultAfAttr, 0))
		# priority
		cmds.text('af_priority_T', l= 'Priority', fn= 'smallPlainLabelFont')
		cmds.intField('af_priority_F', w= 60, v= pm.optionVar.get('af_priority_F_ov', 99))
		cmds.iconTextButton('af_priority_B', w= 20, h= 20, image= 'removeRenderable.png', ann= 'set to default.'
			, c= partial(self.dpaf_setDefaultAfAttr, 1))
		# host mask
		cmds.text('af_hostMask_T', l= 'Host Mask', fn= 'smallPlainLabelFont')
		cmds.textField('af_hostMask_F', w= 147, text= pm.optionVar.get('af_hostMask_F_ov', ''))
		cmds.iconTextButton('af_hostMask_B', w= 20, h= 20, image= 'removeRenderable.png', ann= 'set to default.'
			, c= partial(self.dpaf_setDefaultAfAttr, 2))
		# host exclude mask
		cmds.text('af_hostExcl_T', l= 'Host Exclude', fn= 'smallPlainLabelFont')
		cmds.textField('af_hostExcl_F', w= 147, text= pm.optionVar.get('af_hostExcl_F_ov', ''))
		cmds.iconTextButton('af_hostExcl_B', w= 20, h= 20, image= 'removeRenderable.png', ann= 'set to default.'
			, c= partial(self.dpaf_setDefaultAfAttr, 3))
		# pause close
		cmds.checkBox('af_paused', l= 'Start Paused', v= pm.optionVar.get('af_paused_ov', 0))
		cmds.checkBox('af_close', l= 'Close', v= pm.optionVar.get('af_close_ov', 1))
		# send job btn
		cmds.button('af_sendJbBtn', l= 'S E N D   J O B', bgc= [0.31, 0.45, 0.20], w= 164, h= 30, c= self.launch)

		# set ui position
		st, et, bt = 36, 72-12 ,108-24
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_separate' , 'top', 6 ), ('af_separate' , 'left', 16)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_layerMenu', 'top', 24 ), ('af_layerMenu', 'left', 16)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_refresBtn', 'top', 3 ), ('af_refresBtn', 'left', 3)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_strFrmTxt', 'top', st+19), ('af_strFrmTxt', 'left', 98)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_endFrmTxt', 'top', et+19), ('af_endFrmTxt', 'left', 98)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_stpFrmTxt', 'top', bt+19), ('af_stpFrmTxt', 'left', 98)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_strFrmFfd', 'top', st+14), ('af_strFrmFfd', 'left', 15)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_endFrmFfd', 'top', et+14), ('af_endFrmFfd', 'left', 15)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_stpFrmFfd', 'top', bt+14), ('af_stpFrmFfd', 'left', 15)])

		cmds.formLayout('afanasy_Form', e= 1, af= [('af_strAniBtn', 'top', st+15), ('af_strAniBtn', 'left', 146)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_strPbkBtn', 'top', st+15), ('af_strPbkBtn', 'left', 110)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_endAniBtn', 'top', et+15), ('af_endAniBtn', 'left', 146)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_endPbkBtn', 'top', et+15), ('af_endPbkBtn', 'left', 110)])

		cmds.formLayout('afanasy_Form', e= 1, af= [('af_ResTextB'  , 'top', bt+39+2), ('af_ResTextB'  , 'left' ,13)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_ResTextW'  , 'top', bt+39), ('af_ResTextW'  , 'right' ,100)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_ResTextX'  , 'top', bt+39), ('af_ResTextX'  , 'left' , 90)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_ResTextH'  , 'top', bt+39), ('af_ResTextH'  , 'left' , 101)])

		cmds.formLayout('afanasy_Form', e= 1, af= [('af_cameraTxt', 'top', 24 +  0 + 116), ('af_cameraTxt', 'left', 17)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_cameraScr', 'top', 24 + 14 + 116), ('af_cameraScr', 'left', 15)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_overriBtn', 'top', 24 + 14 + 116), ('af_overriBtn', 'left', 163)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_addCamBtn', 'top', 24 + 33 + 116), ('af_addCamBtn', 'left', 164 if cmds.about(v= 1) == '2016' else 165)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_delCamBtn', 'top', 24 + 52 + 116), ('af_delCamBtn', 'left', 164 if cmds.about(v= 1) == '2016' else 165)])

		cmds.formLayout('afanasy_Form', e= 1, af= [('af_frmPTask_T', 'top',  0 + 223), ('af_frmPTask_T', 'left',  17)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_frmPTask_F', 'top', 14 + 223), ('af_frmPTask_F', 'left',  15)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_frmPTask_B', 'top', 14 + 223), ('af_frmPTask_B', 'left',  77)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_priority_T', 'top',  0 + 223), ('af_priority_T', 'left',  17 + 87)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_priority_F', 'top', 14 + 223), ('af_priority_F', 'left',  15 + 87)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_priority_B', 'top', 14 + 223), ('af_priority_B', 'left',  164)])

		cmds.formLayout('afanasy_Form', e= 1, af= [('af_hostMask_T', 'top',  0 + 223 + 40), ('af_hostMask_T', 'left',  17)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_hostMask_F', 'top', 14 + 223 + 40), ('af_hostMask_F', 'left',  15)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_hostMask_B', 'top', 14 + 223 + 40), ('af_hostMask_B', 'left', 164)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_hostExcl_T', 'top',  0 + 223 + 75), ('af_hostExcl_T', 'left',  17)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_hostExcl_F', 'top', 14 + 223 + 75), ('af_hostExcl_F', 'left',  15)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_hostExcl_B', 'top', 14 + 223 + 75), ('af_hostExcl_B', 'left', 164)])

		cmds.formLayout('afanasy_Form', e= 1, af= [('af_paused', 'top', 170 + 52 + 119), ('af_paused', 'left', 15)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_close' , 'top', 170 + 52 + 119), ('af_close' , 'left', 132)])
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_sendJbBtn', 'top', 195 + 52 + 119), ('af_sendJbBtn', 'left', 13)])

		cmds.setParent( '..' )
		cmds.setParent( '..' )

		self.dpaf_postSceneReadJob()

		#''' makeQtStyle'''
		if set_QtStyle:
			self.dpaf_mainWindow_Qt()
		else:
			cmds.warning('dpaf_Afanasy: This machine can\'t not use PySide.')

		cmds.window(window, e= 1, w= 10, h= 10)
		cmds.showWindow(window)


	def launch(self, *args, **kwargs):
		"""launch renderer command
		"""
		# do nothing if there is no window (called externally)
		if not pm.window('cgru_afanasy_wnd', ex= 1):
			return

		# get values
		separate_layers = pm.checkBox('af_separate', q=1, v=1)
		start_frame = int(pm.floatField('af_strFrmFfd', q=1, v=1))
		end_frame = int(pm.floatField('af_endFrmFfd', q=1, v=1))
		frames_per_task = pm.intField('af_frmPTask_F', q=1, v=1)
		by_frame = int(pm.floatField('af_stpFrmFfd', q=1, v=1))
		hosts_mask = pm.textField('af_hostMask_F', q=1, text=1)
		hosts_exclude = pm.textField('af_hostExcl_F', q=1, text=1)
		priority = pm.intField('af_priority_F', q=1, v=1)
		pause = pm.checkBox('af_paused', q=1, v=1)
		close = pm.checkBox('af_close', q=1, v=1)

		# check values
		if start_frame > end_frame:
			temp = end_frame
			end_frame = start_frame
			start_frame = temp

		frames_per_task = max(1, frames_per_task)
		by_frame = max(1, by_frame)

		# store field values
		pm.optionVar['af_separate_layer_ov'] = separate_layers
		pm.optionVar['af_frmPTask_F_ov'] = frames_per_task
		pm.optionVar['af_hostMask_F_ov'] = hosts_mask
		pm.optionVar['af_hostExcl_F_ov'] = hosts_exclude
		pm.optionVar['af_priority_F_ov'] = priority
		pm.optionVar['af_paused_ov'] = pause
		pm.optionVar['af_close_ov'] = close

		# get paths
		scene_name = pm.sceneName()
		datetime = '%s%s' % (
			time.strftime('%y%m%d-%H%M%S-'),
			str(time.time() - int(time.time()))[2:5]
		)

		filename = '%s.%s.mb' % (scene_name, datetime)

		project_path = pm.workspace(q=1, rootDirectory=1)

		# ############################################################################
		# maya images folder root, a default path for not separate_layers
		# changed by DavidPower
		outputs = pm.workspace(q= 1, rd= 1) + pm.workspace('images', q= 1, fre= 1)
		# ############################################################################

		job_name = os.path.basename(scene_name)

		logger.debug('%ss %se %sr' % (start_frame, end_frame, by_frame))
		logger.debug('scene        = %s' % scene_name)
		logger.debug('file         = %s' % filename)
		logger.debug('job_name     = %s' % job_name)
		logger.debug('project_path = %s' % project_path)
		logger.debug('outputs      = %s' % outputs)

		if pm.checkBox('af_close', q=1, v=1):
			pm.deleteUI('cgru_afanasy_wnd')

		cmd_buffer = [
			'"%(filename)s"',
			'%(start)s',
			'%(end)s',
			'-by %(by_frame)s',
			'-hostsmask "%(msk)s"',
			'-hostsexcl "%(exc)s"',
			'-fpt %(fpt)s',
			'-name "%(name)s"',
			'-priority %(prio)s',
			'-pwd "%(pwd)s"',
			'-proj "%(proj)s"',
			'-images "%(images)s"',
			'-deletescene'
		]

		kwargs = {
			'filename': filename,
			'start': start_frame,
			'end': end_frame,
			'by_frame': by_frame,
			'msk': hosts_mask,
			'exc': hosts_exclude,
			'fpt': frames_per_task,
			'name': job_name,
			'prio': priority,
			'pwd': project_path,
			'proj': project_path,
			'images': outputs
		}

		drg = pm.PyNode('defaultRenderGlobals')
		if drg.getAttr('currentRenderer') == 'mentalRay':
			cmd_buffer.append('-type maya_mental')

		if pause:
			cmd_buffer.append('-pause')

		#-----------------------------#
		currentRenderer = pm.PyNode('defaultRenderGlobals').getAttr('currentRenderer')
		sn = os.path.basename(cmds.file(q= 1, exn= 1)).split('.')[0]
		imgPrefix = pm.getAttr('vraySettings.fileNamePrefix') if currentRenderer == 'vray' else pm.getAttr('defaultRenderGlobals.imageFilePrefix')
		tmpPrefix = imgPrefix.replace('<Scene>', sn)
		if currentRenderer == 'vray':
			pm.setAttr('vraySettings.fileNamePrefix', tmpPrefix)
		else:
			pm.setAttr('defaultRenderGlobals.imageFilePrefix', tmpPrefix)
		#-----------------------------#

		# save file
		pm.saveAs(
			filename,
			force=1,
			type='mayaBinary'
		)

		#-----------------------------#
		if currentRenderer == 'vray':
			pm.setAttr('vraySettings.fileNamePrefix', imgPrefix)
		else:
			pm.setAttr('defaultRenderGlobals.imageFilePrefix', imgPrefix)
		#-----------------------------#

		# rename back to original name
		pm.renameFile(scene_name)

		cmdList = []

		# submit renders
		if separate_layers:
			# render each layer separately
			rlm = pm.PyNode('renderLayerManager')
			layers = [layer for layer in rlm.connections()
					  if layer.renderable.get()]

			for layer in layers:
				layer_name = layer.name()
				kwargs['name'] = '%s:%s' % (job_name, layer_name)

				# ############################################################################
				# update images path for each layers, and fix outputs if renderer is vray
				# changed by DavidPower
				kwargs['images'] = self.dpaf_outputsFix(layer)
				# ############################################################################

				kwargs['start'] = int(self.dpaf_getOverrideData('defaultRenderGlobals.startFrame', layer_name))
				kwargs['end'] = int(self.dpaf_getOverrideData('defaultRenderGlobals.endFrame', layer_name))
				kwargs['by_frame'] = int(self.dpaf_getOverrideData('defaultRenderGlobals.byFrameStep', layer_name))

				tmp_cmd_buffer = copy.copy(cmd_buffer)
				tmp_cmd_buffer.append(
					'-take %s' % layer.name()
				)

				# create one big command
				afjob_cmd = ' '.join([
					os.environ['CGRU_PYTHONEXE'],
					'"%s/python/afjob.py"' % os.environ['AF_ROOT'],
					'%s' % ' '.join(tmp_cmd_buffer) % kwargs
				])
				cmdList.append(afjob_cmd)

		else:
			# create one big command
			afjob_cmd = ' '.join([
				os.environ['CGRU_PYTHONEXE'],
				'%s/python/afjob.py' % os.environ['AF_ROOT'],
				'%s' % ' '.join(cmd_buffer) % kwargs
			])
			cmdList.append(afjob_cmd)

		# call each command separately
		for cmd in cmdList:
			print(cmdList)

			os.system(cmd)


	def dpaf_outputsFix(self, layer):
		"""fix image output path if renderer is vray

		:param layer: maya renderLayer name
		:return outputs_Fixed: correct image output path
		"""
		outputs_Fixed = ''
		currentRenderer = pm.PyNode('defaultRenderGlobals').getAttr('currentRenderer')

		# get current maya image format setting
		tmp_OutFormatControl = pm.getAttr('defaultRenderGlobals.outFormatControl') if currentRenderer == 'vray' else ''
		imgPrefix_vray = pm.getAttr('vraySettings.fileNamePrefix') if currentRenderer == 'vray' else ''
		imgPrefix_maya = pm.getAttr('defaultRenderGlobals.imageFilePrefix') if currentRenderer == 'vray' else ''
		imageFormatStr = ('.' + ('png' if not pm.getAttr('vraySettings.imageFormatStr') else pm.getAttr('vraySettings.imageFormatStr'))) if currentRenderer == 'vray' else ''
		
		if currentRenderer == 'vray':
			# change current setting for fixing vray output path
			pm.setAttr('defaultRenderGlobals.outFormatControl', 1)
			pm.setAttr('defaultRenderGlobals.imageFilePrefix', imgPrefix_vray if imgPrefix_vray else '', type= 'string') if imgPrefix_vray else None

		# write output path
		outputs_Fixed = pm.renderSettings(layer= layer, fullPath= 1, firstImageName= 1, lastImageName= 1)
		outputs_Fixed[0] = os.path.normpath(outputs_Fixed[0]) + imageFormatStr
		outputs_Fixed[1] = os.path.normpath(outputs_Fixed[1]) + imageFormatStr
		outputs_Fixed = ','.join(outputs_Fixed)

		if currentRenderer == 'vray':
			# restore previous setting for good
			pm.setAttr('defaultRenderGlobals.imageFilePrefix', imgPrefix_maya if imgPrefix_maya else '', type= 'string') if imgPrefix_vray else None
			pm.setAttr('defaultRenderGlobals.outFormatControl', tmp_OutFormatControl)

		return outputs_Fixed


	def dpaf_mainWindow_Qt(self):

		self.dpaf_makePySideUI('af_refresBtn', 'QPushButton {border: 1px solid OliveDrab; border-radius: 2px;}')
		self.dpaf_makePySideUI('af_strAniBtn', 'QPushButton {border: 1px solid DimGray; color: DimGray; border-radius: 5px;}')
		self.dpaf_makePySideUI('af_strPbkBtn', 'QPushButton {border: 1px solid Gray; color: Gray; border-radius: 5px;}')
		self.dpaf_makePySideUI('af_endAniBtn', 'QPushButton {border: 1px solid DimGray; color: DimGray; border-radius: 5px;}')
		self.dpaf_makePySideUI('af_endPbkBtn', 'QPushButton {border: 1px solid Gray; color: Gray; border-radius: 5px;}')
		self.dpaf_makePySideUI('af_sendJbBtn', 'QPushButton {border: 1px solid SeaGreen; color: SeaGreen; background-color: #3F3F3F; border-radius: 4px;}')


	def dpaf_setRendererName(self, renderer):

		def dpaf_rendName_InfoFormat(renderer, qType):
	
			if renderer == 'mentalRay' :
				if qType == 'name' : return 'Mental Ray'
				if qType == 'space' : return '56'
			elif renderer == 'mayaVector' :
				if qType == 'name' : return 'Maya Vector'
				if qType == 'space' : return '53'
			elif renderer == 'mayaHardware2' :
				if qType == 'name' : return 'Maya Hardware 2.0'
				if qType == 'space' : return '36'
			elif renderer == 'mayaHardware' :
				if qType == 'name' : return 'Maya Hardware'
				if qType == 'space' : return '47'
			elif renderer == 'mayaSoftware' :
				if qType == 'name' : return 'Maya Software'
				if qType == 'space' : return '48'
			elif renderer == 'vray' :
				if qType == 'name' : return 'V-Ray'
				if qType == 'space' : return '74'
			elif renderer == 'arnold' :
				if qType == 'name' : return 'Arnold'
				if qType == 'space' : return '71'
			else :
				if qType == 'name' : return 'my Render'
				if qType == 'space' : return '59'

		global dpaf_keepRendererNameDisplayCorrectly

		if renderer == 'current':
			renderer = cmds.getAttr('defaultRenderGlobals.currentRenderer')

		currentLayer = cmds.editRenderLayerGlobals(q= 1, currentRenderLayer= 1)
		layer = cmds.optionMenu('af_layerMenu', q= 1, v= 1)
		if not layer.startswith('-'):
			if layer == 'No Renderable Layer' or layer == 'masterLayer': layer = 'defaultRenderLayer'
			if dpaf_keepRendererNameDisplayCorrectly or layer == currentLayer:
				cmds.frameLayout('afanasy_Frame', e= 1, l= dpaf_rendName_InfoFormat(renderer, 'name'), li= int(dpaf_rendName_InfoFormat(renderer, 'space')))
				dpaf_keepRendererNameDisplayCorrectly = 0


	def dpaf_layerMenuSync(self, *args):

		# get current layer, direct using pyhton cmd when sceneQueue changing file will cause error, reason unknow.
		try:
			currentLayer = cmds.editRenderLayerGlobals(q= 1, currentRenderLayer= 1)
		except:
			currentLayer = mel.eval('editRenderLayerGlobals -q -currentRenderLayer')
		
		try:
			cmds.optionMenu('af_layerMenu', e= 1, v= currentLayer if currentLayer != 'defaultRenderLayer' else 'masterLayer')
		except:
			pass

		if cmds.optionMenu('af_layerMenu', q= 1, v= 1) == 'masterLayer': cmds.iconTextButton('af_overriBtn', e= 1, image= 'overrideSettings_dim.png')
		
		self.dpaf_rangeCtrlGetLayerAttr()


	def dpaf_changeResolution(self, *args):

		cmds.text('af_ResTextW', e= 1, l= str(int(cmds.getAttr('defaultResolution.width'))))
		cmds.text('af_ResTextH', e= 1, l= str(int(cmds.getAttr('defaultResolution.height'))))


	def dpaf_separateLayerAdj(self, *args):

		if cmds.checkBox('af_separate', q= 1, v= 1):
			cmds.optionMenu('af_layerMenu', e= 1, en= 1)
			self.dpaf_refreshLayerMenu()
		else:
			layer = cmds.optionMenu('af_layerMenu', q= 1, v= 1)
			if cmds.optionMenu('af_layerMenu', q= 1, ni= 1):
				for item in cmds.optionMenu('af_layerMenu', q= 1, ils= 1):
					cmds.deleteUI(item)
			cmds.menuItem('af_layerMenuItem_noSeparateLayer', l= '- ' + layer, p= 'af_layerMenu')
			cmds.optionMenu('af_layerMenu', e= 1, en= 0)


	def dpaf_setTimeLineRange(self, attrName, ctrlPrefix, flag, *args):

		cmds.floatField(ctrlPrefix + 'Ffd', e= 1, v= mel.eval('playbackOptions -q -' + flag ))
		self.dpaf_setAttrSync(attrName, ctrlPrefix)


	def dpaf_setDefaultAfAttr(self, op):

		if op == 0:
			cmds.intField('af_frmPTask_F', e= 1, v= 1)
		if op == 1:
			cmds.intField('af_priority_F', e= 1, v= 99)
		if op == 2:
			cmds.textField('af_hostMask_F', e= 1, text= '')
		if op == 3:
			cmds.textField('af_hostExcl_F', e= 1, text= '')


	def dpaf_init_Resolution(self):

		mel.eval('setTestResolutionVar(1)')
		self.dpaf_changeResolution()


	def dpaf_layerRenderableTracker(self, layerOldName):

		global dpaf_unRenderableLayers

		try:
			tmp_undoInfo = cmds.undoInfo(q= 1, un= 1)
			layer = tmp_undoInfo.split()[-2].split('"')[1]
			value = tmp_undoInfo.split()[-1].split('"')[1]
			# store the undoInfo into Mel global for other procedure use
			mel.eval('global string $tmp_undoInfo = "' + cmds.encodeString(tmp_undoInfo) + '";')
		except:
			try:
				# try to load Mel global for undoInfo, if undoInfo has been flushed by other procedure
				tmp_undoInfo = mel.eval('$tmp = $tmp_undoInfo;')
				layer = tmp_undoInfo.split()[-2].split('"')[1]
				value = tmp_undoInfo.split()[-1].split('"')[1]
			except:
				layer = 'defaultRenderLayer' if cmds.optionMenu('af_layerMenu', q= 1, v= 1) == 'masterLayer' else cmds.optionMenu('af_layerMenu', q= 1, v= 1)
				value = cmds.getAttr(layer + '.renderable')
				if 'af_layerMenuItem_' + layer in cmds.optionMenu('af_layerMenu', q=1, ils= 1):
					cmds.deleteUI('af_layerMenuItem_' + layer)
				if cmds.optionMenu('af_layerMenu', q= 1, ni= 1) == 0:
					cmds.menuItem('af_layerMenuItem_NoRenderableLayer', l= 'No Renderable Layer', p= 'af_layerMenu')
					cmds.optionMenu('af_layerMenu', e= 1, en= 0)

		if int(value):
			if cmds.optionMenu('af_layerMenu', q= 1, v= 1) == 'No Renderable Layer':
				cmds.deleteUI('af_layerMenuItem_NoRenderableLayer')
				cmds.optionMenu('af_layerMenu', e= 1, en= 1)
			if layer in dpaf_unRenderableLayers: dpaf_unRenderableLayers.remove(layer)
			cmds.menuItem('af_layerMenuItem_' + layer, l= layer if layer != 'defaultRenderLayer' else 'masterLayer', p= 'af_layerMenu')
			if layer != 'defaultRenderLayer':
				cmds.scriptJob(ro= 1, ac= [layer + '.renderable', partial(self.dpaf_layerRenderableTracker, layer)], p= 'af_layerMenuItem_' + layer)
				cmds.scriptJob(nodeNameChanged= [layer, partial(self.dpaf_layerReNameTracker, layer)], p= 'af_layerMenuItem_' + layer)
			if layer == cmds.editRenderLayerGlobals(q= 1, currentRenderLayer= 1):
				cmds.optionMenu('af_layerMenu', e= 1, v= layer if layer != 'defaultRenderLayer' else 'masterLayer')
		else:
			cmds.deleteUI('af_layerMenuItem_' + layerOldName)
			if layer not in dpaf_unRenderableLayers: dpaf_unRenderableLayers.append(layer)
			if layer != 'defaultRenderLayer':
				cmds.scriptJob(ro= 1, ac= [layer + '.renderable', partial(self.dpaf_layerRenderableTracker, layer)], p= 'cgru_afanasy_wnd')
			if cmds.optionMenu('af_layerMenu', q= 1, ni= 1) == 0:
				cmds.menuItem('af_layerMenuItem_NoRenderableLayer', l= 'No Renderable Layer', p= 'af_layerMenu')
				cmds.optionMenu('af_layerMenu', e= 1, en= 0)

		self.dpaf_layerMenuSync()


	def dpaf_layerReNameTracker(self, layerOldName):

		layer = cmds.undoInfo(q= 1, un= 1).split()[-1].split('"')[1]
		cmds.menuItem('af_layerMenuItem_' + layerOldName, e= 1, l= layer)


	def dpaf_refreshLayerMenu(self, *args):

		global dpaf_unRenderableLayers
		
		# if I don't print something, scriptJob [renderLayerChange] may not work sometimes, ex: deleting the only (v)renderLayer except (x)masterLayer 
		print 'dpaf_Afanasy: Refreshing layer optionMenu...'

		if cmds.optionMenu('af_layerMenu',q= 1, ni= 1):
			for item in cmds.optionMenu('af_layerMenu', q= 1, ils= 1):
				cmds.deleteUI(item)

		for layer in cmds.ls(et= 'renderLayer'):
			if cmds.getAttr(layer + '.renderable'):
				if layer in dpaf_unRenderableLayers: dpaf_unRenderableLayers.remove(layer)
				cmds.menuItem('af_layerMenuItem_' + layer, l= layer if layer != 'defaultRenderLayer' else 'masterLayer', p= 'af_layerMenu')
				if layer != 'defaultRenderLayer':
					cmds.scriptJob(ro= 1, ac= [layer + '.renderable', partial(self.dpaf_layerRenderableTracker, layer)], p= 'af_layerMenuItem_' + layer)
					cmds.scriptJob(nodeNameChanged= [layer, partial(self.dpaf_layerReNameTracker, layer)], p= 'af_layerMenuItem_' + layer)
			else:
				if layer not in dpaf_unRenderableLayers: dpaf_unRenderableLayers.append(layer)
				if layer != 'defaultRenderLayer':
					cmds.scriptJob(ro= 1, ac= [layer + '.renderable', partial(self.dpaf_layerRenderableTracker, layer)], p= 'cgru_afanasy_wnd')

		currentLayer = cmds.editRenderLayerGlobals(q= 1, currentRenderLayer= 1)
		if cmds.optionMenu('af_layerMenu', q= 1, ni= 1):
			if 'af_layerMenuItem_' + currentLayer in cmds.optionMenu('af_layerMenu', q= 1, ils= 1):
				cmds.optionMenu('af_layerMenu', e= 1, v= currentLayer if currentLayer != 'defaultRenderLayer' else 'masterLayer')
			cmds.optionMenu('af_layerMenu', e= 1, en= 1)
		else:
			cmds.menuItem('af_layerMenuItem_NoRenderableLayer', l= 'No Renderable Layer', p= 'af_layerMenu')
			cmds.optionMenu('af_layerMenu', e= 1, en= 0)

		self.dpaf_layerMenuSync()


	def dpaf_frameRangePopupMenuPostCmd(self, attrName, textName, *args):

		layer = cmds.optionMenu('af_layerMenu', q= 1, v= 1)
		if layer == 'No Renderable Layer' or layer.startswith('-'): layer = 'masterLayer'
		if layer != 'masterLayer':
			cmds.popupMenu('af_' + attrName.split('.')[1] + '_popupMenu', e= 1, dai= 1)
			if self.dpaf_hasOverride(attrName, layer):
				cmds.menuItem(l= 'Remove Layer Override', c= partial(self.dpaf_frameRangeMenuItemCmd, attrName, textName, layer, 1), p= 'af_' + attrName.split('.')[1] + '_popupMenu')
			else:
				cmds.menuItem(l= 'Create Layer Override', c= partial(self.dpaf_frameRangeMenuItemCmd, attrName, textName, layer, 0), p= 'af_' + attrName.split('.')[1] + '_popupMenu')


	def dpaf_frameRangeMenuItemCmd(self, attrName, textName, layer, remove, *args):

		if remove:
			cmds.editRenderLayerAdjustment(attrName, lyr= layer, r= 1)
			self.dpaf_tintOverrideColor(textName, 0)
		else:
			cmds.editRenderLayerAdjustment(attrName, lyr= layer)
			self.dpaf_tintOverrideColor(textName, 1)


	def dpaf_tintOverrideColor(self, textName, tint, *args):

		#pySide
		if tint:
			if set_QtStyle:
				self.dpaf_makePySideUI(textName, 'QLabel {color: Chocolate}')
			else:
				pass
		else:
			if set_QtStyle:
				self.dpaf_makePySideUI(textName, 'QLabel {color: None}')
			else:
				pass


	def dpaf_setAttrSync(self, attrName, ctrlPrefix, *args):

		layer = cmds.optionMenu('af_layerMenu', q= 1, v= 1)
		if layer == 'No Renderable Layer' or layer.startswith('-'): layer = 'masterLayer'
		layer = 'defaultRenderLayer' if layer == 'masterLayer' else layer
		
		self.dpaf_setOverrideData(attrName, layer, cmds.floatField(ctrlPrefix + 'Ffd', q= 1, v= 1))
		cmds.floatField(ctrlPrefix + 'Ffd', e= 1, v= self.dpaf_getOverrideData(attrName, layer))


	def dpaf_rangeCtrlGetLayerAttr(self, *args):

		global dpaf_keepRendererNameDisplayCorrectly
		dpaf_keepRendererNameDisplayCorrectly = 1

		self.dpaf_getAttrSync('defaultRenderGlobals.startFrame', 'af_strFrm')
		self.dpaf_getAttrSync('defaultRenderGlobals.endFrame', 'af_endFrm')
		self.dpaf_getAttrSync('defaultRenderGlobals.byFrameStep', 'af_stpFrm')
		self.dpaf_getCameraList()

		layer = cmds.optionMenu('af_layerMenu', q= 1, v= 1)
		if layer == 'No Renderable Layer' or layer.startswith('-') or layer == 'masterLayer': layer = 'defaultRenderLayer'
		self.dpaf_setRendererName(self.dpaf_getOverrideData('defaultRenderGlobals.currentRenderer', layer))


	def dpaf_getAttrSync(self, attrName, ctrlPrefix):
		
		layer = cmds.optionMenu('af_layerMenu', q= 1, v= 1)
		if layer == 'No Renderable Layer' or layer.startswith('-') or layer == 'masterLayer': layer = 'defaultRenderLayer'
		
		if layer == cmds.editRenderLayerGlobals(q= 1, currentRenderLayer= 1):
			# Reason for doing this is because when layerOptionMenu query overrided frame value in current layer,
			# the value(sec) store in '.value' and '.plug' have a slightly different.
			# Still not very clearly why, but for now, this way do well. 
			value = cmds.getAttr(attrName)
		else:
			value = self.dpaf_getOverrideData(attrName, layer)

		cmds.floatField(ctrlPrefix + 'Ffd', e= 1, v= value)

		if layer != 'defaultRenderLayer' and self.dpaf_hasOverride(attrName, layer):
			self.dpaf_tintOverrideColor(ctrlPrefix + 'Txt', 1)
		else:
			self.dpaf_tintOverrideColor(ctrlPrefix + 'Txt', 0)


	def dpaf_getCameraList(self):

		cmds.iconTextButton('af_addCamBtn', e= 1, image= 'openAttribute.png', c= self.dpaf_disrenderableCameraList)
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_addCamBtn', 'top', 24 + 33 + 116), ('af_addCamBtn', 'left', 164 if cmds.about(v= 1) == '2016' else 165)])
		#pySide
		if set_QtStyle:
			self.dpaf_makePySideUI('af_cameraScr', 'QListView {color: None}')
		else:
			pass
		layer = cmds.optionMenu('af_layerMenu', q= 1, v= 1)
		if layer == 'No Renderable Layer' or layer.startswith('-'): layer = 'masterLayer'
		layer = 'defaultRenderLayer' if layer == 'masterLayer' else layer
		cmds.textScrollList('af_cameraScr', e= 1, ra= 1)
		for cam in cmds.ls(ca= 1):
			if self.dpaf_getOverrideData(cam + '.renderable', layer):
				cmds.textScrollList('af_cameraScr', e= 1, a= cmds.listRelatives(cam, p= 1))


	def dpaf_disrenderableCameraList(self, *args):

		cmds.iconTextButton('af_addCamBtn', e= 1, image= 'currentNamespace.png', c= partial(self.dpaf_adjRenderCamera, 1))
		cmds.formLayout('afanasy_Form', e= 1, af= [('af_addCamBtn', 'top', 24 + 34 + 116), ('af_addCamBtn', 'left', 164 if cmds.about(v= 1) == '2016' else 163)])
		#pySide
		if set_QtStyle:
			self.dpaf_makePySideUI('af_cameraScr', 'QListView {color: MediumSpringGreen; border-radius: 3px; border: 2px solid SeaGreen;}')
		else:
			pass
		layer = cmds.optionMenu('af_layerMenu', q= 1, v= 1)
		if layer == 'No Renderable Layer' or layer.startswith('-'): layer = 'masterLayer'
		layer = 'defaultRenderLayer' if layer == 'masterLayer' else layer
		cmds.textScrollList('af_cameraScr', e= 1, ra= 1)
		for cam in cmds.ls(ca= 1):
			if not self.dpaf_getOverrideData(cam + '.renderable', layer):
				cmds.textScrollList('af_cameraScr', e= 1, a= cmds.listRelatives(cam, p= 1))


	def dpaf_adjRenderCamera(self, value, *args):

		layer = cmds.optionMenu('af_layerMenu', q= 1, v= 1)
		if layer == 'No Renderable Layer' or layer.startswith('-'): layer = 'masterLayer'
		layer = 'defaultRenderLayer' if layer == 'masterLayer' else layer
		override = 0 if '_dim' in cmds.iconTextButton('af_overriBtn', q= 1, image= 1) else 1
		# geather selected camera
		camerAdjList = cmds.textScrollList('af_cameraScr', q= 1, si= 1)
		if camerAdjList:
			for cam in camerAdjList:
				cmaShapeAttr = cmds.listRelatives(cam, s= 1)[0] + '.renderable'
				if override and layer != 'defaultRenderLayer': cmds.editRenderLayerAdjustment(cmaShapeAttr, lyr= layer)
				self.dpaf_setOverrideData(cmaShapeAttr, layer, value)

		self.dpaf_getCameraList()


	def dpaf_removeCamOverride(self, allLayer, *args):

		camerAdjList = cmds.textScrollList('af_cameraScr', q= 1, si= 1)
		if camerAdjList:
			for cam in camerAdjList:
				cmaShapeAttr = cmds.listRelatives(cam, s= 1)[0] + '.renderable'
				if allLayer:
					for layer in cmds.listConnections(cmaShapeAttr, p= 1):
						layer = layer.split('.')[0]
						if layer != 'defaultRenderLayer':
							cmds.editRenderLayerAdjustment(cmaShapeAttr, lyr= layer, r= 1)
				else:
					layer = cmds.optionMenu('af_layerMenu', q= 1, v= 1)
					if layer == 'No Renderable Layer' or layer.startswith('-'): layer = 'masterLayer'
					if layer != 'masterLayer':
						cmds.editRenderLayerAdjustment(cmaShapeAttr, lyr= layer, r= 1)

			self.dpaf_getCameraList()


	def dpaf_makePySideUI(self, ctrlName, myStyle):

		# thanks to Nathan Horne
		ctrlName = long(MQtUtil.findControl(ctrlName))
		qObj = wrapInstance(ctrlName, QtCore.QObject)
		metaObj = qObj.metaObject()
		cls = metaObj.className()
		superCls = metaObj.superClass().className()

		if hasattr(QtGui, cls):
			base = getattr(QtGui, cls)
		elif hasattr(QtGui, superCls):
			base = getattr(QtGui, superCls)
		else:
			base = QtGui.QWidget

		uiPySide = wrapInstance(ctrlName, base)
		uiPySide.setStyleSheet(myStyle)


	def dpaf_postSceneReadJob(self):
		
		self.dpaf_separateLayerAdj()
		self.dpaf_setRendererName('current')
		self.dpaf_init_Resolution()

		# scenes switching engine
		cmds.scriptJob(e= ['PostSceneRead', self.dpaf_postSceneReadJob], ro= 1, p= 'cgru_afanasy_wnd')


	def dpaf_setOverrideData(self, setValue, setlayer, value):
		# set override value without switching layers : it can set everything! (setValue = 'object.attribute' or 'fps') # dataType problem
		destination = setValue
		overrideList = cmds.listConnections(setValue, p= 1) if setValue != 'fps' else []
		setFrame = 1 if setValue == 'defaultRenderGlobals.startFrame' or setValue == 'defaultRenderGlobals.endFrame' else 0
		atCurrentLayer = 1 if cmds.editRenderLayerGlobals(q= 1, currentRenderLayer= 1) == setlayer else 0
		goWithMaster = 1 if cmds.editRenderLayerGlobals(q= 1, currentRenderLayer= 1) == 'defaultRenderLayer' and not self.dpaf_hasOverride(setValue, setlayer) else 0
		# if this attr has override by some layer(s)
		if overrideList and not atCurrentLayer and not goWithMaster:
			# find override
			setLayerProx = setlayer
			findOverride = 0

			while findOverride == 0:
				for override in overrideList:
					Buffer = override.split('.')
					if Buffer[0] == setLayerProx:
						destination = Buffer[0] + '.' + Buffer[1] + '.value'
						findOverride = 1
						break
				# if this layer has no override, change setlayer to defaultLayer(masterLayer)
				setLayerProx = 'defaultRenderLayer' if findOverride == 0 else setLayerProx
		
		if setFrame and destination.endswith('.value'):
			timeUnit = cmds.currentUnit(q= 1, t= 1) # mel.eval('currentTimeUnitToFPS')
			if timeUnit[-3:] == 'fps':
				value = round(value * (6000.0 / float(timeUnit.split('fps')[0])), 0) / 6000.0
			value = {		# maya stores 'ticks/tps' behind, vvv-> value = int(frame * tpf) / tps
					'game' : round(value * 400, 0) / 6000.0,
					'film' : round(value * 250, 0) / 6000.0,
					 'pal' : round(value * 240, 0) / 6000.0,
					'ntsc' : round(value * 200, 0) / 6000.0,
					'show' : round(value * 125, 0) / 6000.0,
					'palf' : round(value * 120, 0) / 6000.0,
				   'ntscf' : round(value * 100, 0) / 6000.0,
				'millisec' : round(value *   6, 0) / 6000.0,
					 'sec' : round(value * 6000, 0) / 6000.0,
					 'min' : round(value * 360000, 0) / 6000.0,
					'hour' : round(value * 21600000, 0) / 6000.0,
			}.get(timeUnit, value)
		
		if setValue == 'fps':
			try:
				cmds.currentUnit(t= value)
				return 1
			except:
				timeUnitList = ['game', 'film', 'pal', 'ntsc', 'show', 'palf', 'ntscf', 'millisec', 'sec', 'min', 'hour',
								'2fps', '3fps', '4fps', '5fps', '6fps', '8fps', '10fps', '12fps', '16fps', '20fps', '40fps',
								'75fps', '80fps', '100fps', '120fps', '125fps', '150fps', '200fps', '240fps', '250fps', '300fps',
								'375fps', '400fps', '500fps', '600fps', '750fps', '1200fps', '1500fps', '2000fps', '3000fps', '6000fps']
				print '\nTime Unit List:'
				print '	' + '\n	'.join(timeUnitList)
				cmds.warning('dpaf_Afanasy: def dpaf_setOverrideData:: \'fps\' value input error, for more info please check scriptEditor.')
				return 0
		else:
			try:
				cmds.setAttr(destination, value)
				return 1
			except:
				cmds.warning('dpaf_Afanasy: def dpaf_setOverrideData:: attribute setting failed, maybe attr is locked or else...')
				return 0


	def dpaf_getOverrideData(self, queryValue, queryLayer):
		# query override value without switching layers : it can query everything! (queryValue = 'object.attribute' or 'fps') # dataType problem?
		value = ''
		overrideList = cmds.listConnections(queryValue, p= 1) if queryValue != 'fps' else ['fps']
		# if this attr has override by some layer(s)
		if overrideList:
			# find override
			queryLayerProx = queryLayer
			findOverride = 0
			
			while findOverride == 0 and queryValue != 'fps':
				for override in overrideList:
					Buffer = override.split('.')
					if Buffer[0] == queryLayerProx:
						value = cmds.getAttr(Buffer[0] + '.' +Buffer[1] + '.plug')
						if cmds.editRenderLayerGlobals(q= 1, currentRenderLayer= 1) == 'defaultRenderLayer':
							if self.dpaf_hasOverride(queryValue, queryLayer) and queryLayer != 'defaultRenderLayer':
								value = cmds.getAttr(Buffer[0] + '.' +Buffer[1] + '.value')
						else:
							if self.dpaf_hasOverride(queryValue, queryLayerProx) and cmds.editRenderLayerGlobals(q= 1, currentRenderLayer= 1) != queryLayer:
								if self.dpaf_hasOverride(queryValue, queryLayer) or self.dpaf_hasOverride(queryValue, cmds.editRenderLayerGlobals(q= 1, currentRenderLayer= 1)):
									if queryLayer != 'defaultRenderLayer':
										value = cmds.getAttr(Buffer[0] + '.' +Buffer[1] + '.value')
									else:
										if self.dpaf_hasOverride(queryValue, cmds.editRenderLayerGlobals(q= 1, currentRenderLayer= 1)):
											value = cmds.getAttr(Buffer[0] + '.' +Buffer[1] + '.value')
						findOverride = 1
						break		
				# if this layer has no override, change queryLayer to defaultLayer(masterLayer)
				queryLayerProx = 'defaultRenderLayer' if findOverride == 0 else queryLayerProx
			# return value
			if queryValue == 'defaultRenderGlobals.startFrame' or queryValue == 'defaultRenderGlobals.endFrame' or queryValue == 'fps':
				timeUnit = cmds.currentUnit(q= 1, t= 1) # mel.eval('currentTimeUnitToFPS')
				if timeUnit[-3:] == 'fps':
					value = round(round(value * 6000, 0) / (6000 / float(timeUnit.split('fps')[0])), 3) if queryValue != 'fps' else float(timeUnit.split('fps')[0])
				return {		# maya stores 'ticks/tps'(sec) behind, vvv-> frame = int(sec * tps) / tpf
						'game' : round(round(value * 6000, 0) / 400, 3)	if queryValue != 'fps' else 15.0,
						'film' : round(round(value * 6000, 0) / 250, 3)	if queryValue != 'fps' else 24.0,
						 'pal' : round(round(value * 6000, 0) / 240, 3)	if queryValue != 'fps' else 25.0,
						'ntsc' : round(round(value * 6000, 0) / 200, 3)	if queryValue != 'fps' else 30.0,
						'show' : round(round(value * 6000, 0) / 125, 3)	if queryValue != 'fps' else 48.0,
						'palf' : round(round(value * 6000, 0) / 120, 3)	if queryValue != 'fps' else 50.0,
					   'ntscf' : round(round(value * 6000, 0) / 100, 3)	if queryValue != 'fps' else 60.0,
					'millisec' : round(round(value * 6000, 0) /   6, 3) if queryValue != 'fps' else 1000.0,
						 'sec' : round(round(value * 6000, 0) / 6000, 3) if queryValue != 'fps' else (1/1.0),
						 'min' : round(round(value * 6000, 0) / 360000, 3) if queryValue != 'fps' else (1/60.0),
						'hour' : round(round(value * 6000, 0) / 21600000, 3) if queryValue != 'fps' else (1/3600.0),
				}.get(timeUnit, value)
			else:
				return value
		else:
			return cmds.getAttr(queryValue)


	def dpaf_hasOverride(self, queryValue, queryLayer):
		# checking value has overrided or not
		attrList = cmds.editRenderLayerAdjustment(queryLayer, q= 1, lyr= 1)
		has = 0
		if attrList:
			for attr in attrList:
				if attr == queryValue:
					has = 1 
					break
		return has


	def dpaf_refreshLayerMenu_warning(self, *args):

		cmds.warning('dpaf_Afanasy: Refreshing layer optionMenu...')
		self.dpaf_refreshLayerMenu()
		cmds.warning('dpaf_Afanasy: Layer optionMenu refreshed.')
