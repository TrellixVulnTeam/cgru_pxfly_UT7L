import os
import subprocess
import shutil

import cgruconfig
import cgruupdate

def copyFile(src, dst):
	try:
		shutil.copy(src, dst)
		return 0
	except:
		return 1

Files = dict()
updat_success = True
changelogFile = 'changelog.json'
cgru_updateserver = os.getenv('CGRU_UPDATESERVER', cgruconfig.VARS['CGRU_UPDATESERVER'])
cgru_location = os.path.basename(cgruconfig.VARS['CGRU_LOCATION'])
changelog = '\\\\' + cgru_updateserver + '\\' + cgru_location + '\\' + changelogFile
tmp_updateDir = cgruconfig.VARS['CGRU_LOCATION'] + '\\update'
cgruVer = cgruconfig.VARS['CGRU_VERSION']

if not os.path.isdir(tmp_updateDir):
	os.mkdir(tmp_updateDir)


src = changelog
dst = tmp_updateDir
retCode_0 = copyFile(src, dst)
updateList = []
if retCode_0 == 0:
	changelog = tmp_updateDir + '\\' + changelogFile
	cgruupdate.ChangeLog(Files, changelog)
	subVer = '.'.join(cgruVer.split('.')[-3:])
	for logDate in Files:
		if logDate > subVer:
			updateList.append(logDate)
	updateList.sort() # for Dict

	if updateList:
		fileList = []
		for logDate in updateList:
			fileList.extend(Files[logDate])
		fileList = list(set(fileList))

		if fileList is not None:
			for obj in fileList:
				src = '\\\\' + cgru_updateserver + '\\' + cgru_location + obj
				dst = tmp_updateDir
				retCode_1 = copyFile(src, dst)
				if retCode_1 == 0:
					src = tmp_updateDir + '\\' + os.path.basename(obj)
					dst = cgruconfig.VARS['CGRU_LOCATION'] + obj
					retCode_2 = copyFile(src, dst)
					if retCode_2 != 0:
						updat_success = False
						break
				else:
					updat_success = False
					break
		else:
			updat_success = False
	else:
		pass
else:
	updat_success = False


if updat_success:
	if updateList:
		cgruVer_updated = '.'.join(cgruVer.split('.')[:3]) + '.' + updateList[-1]
		with open(cgruconfig.VARS['CGRU_LOCATION'] + '\\version.txt', 'w') as f:
			f.write(cgruVer_updated)
	shutil.rmtree(tmp_updateDir)
	cgruconfig.VARS['CGRU_UPDATE_CMD'] = None
	# restart
	subprocess.call([cgruconfig.VARS['CGRU_LOCATION'] + '\\start.cmd'])

else:
	pass