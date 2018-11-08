import os
from src import reader

def walkingDir(src, IGNORE_dir=[], IGNORE_fileType = []):

	files = []
	dirs = []

	if os.path.isfile(src):
		return [src]

	first_list = [src + '/' + i for i in os.listdir(src)]
	for file in first_list:
		if os.path.isdir(file):
			dirs.append(file)

		else:
			files.append(file)

	# Loop to get all sub files and folders.
	dirs_temp = dirs[:]
	while (len(dirs_temp) > 0):
		i = dirs_temp.pop(0)

		subfolder = [i + '/' + j for j in os.listdir(i) if os.path.isdir(i + '/' + j)]
		subfiles = [i + '/' + j for j in os.listdir(i) if os.path.isfile(i + '/' + j)]

		dirs = dirs + subfolder
		files = files + subfiles

		dirs_temp = dirs_temp + subfolder

	# Exclude ignore files and folders.
	exclude_dir = []
	for folder in dirs:
		if os.path.basename(folder) in IGNORE_dir:
			exclude_dir.append(folder)

	for file in files[:]:
		if os.path.splitext(file)[1] in IGNORE_fileType:
			files.remove(file)

		for each in exclude_dir:
			if each in file:
				files.remove(file)

	return files

def configData():
	return None

def read(file_path):
	return reader.read(filepath)
