import re
import os
import json
import yaml

def read(file_path):

	if os.path.splitext(file_path)[-1] == '.json':
		return _readJson(file_path)
	elif os.path.splitext(file_path)[-1] == '.yml' or os.path.splitext(file_path)[-1] == '.yaml':
		return _readYaml(file_path)

def _readJson(file_path):
	try:
		with open(file_path, 'r') as f:
			json_string = f.read()
			f.close()

	except IOError as e:
		raise e
	except Exception as e:
		raise e

	try:
		# Remove commens from JSON (makes sample config options easier)
		regex = r'\s*(#|\/{2}).*$'
		regex_inline = r'(:?(?:\s)*([A-Za-z\d\.{}]*)|((?<=\").*\"),?)(?:\s)*(((#|(\/{2})).*)|)$'
		lines = json_string.split('\n')

		for index, line in enumerate(lines):
			if re.search(regex, line):
				if re.search(r'^' + regex, line, re.IGNORECASE):
					lines[index] = ""
				elif re.search(regex_inline, line):
					lines[index] = re.sub(regex_inline, r'\1', line)

		data = json.loads('\n'.join(lines))

	except ValueError as e:
		print e
		if os.path.exists(file_path):
			raise SyntaxError("Please check your json syntax : " + file_path)
		else :
			raise IOError("File not found" + file_path)

	except Exception as e:
		raise e

	return data

def _readYaml(file_path):
	with open(file_path, 'r') as f :
		data = yaml.load(f)
		f.close()
	return data

if __name__ == '__main__':
	file_path = "C:/Users/nook/META/SCRIPTS/MEME/memeLauncher/projects/COMMON/configure.yml"
	print read(file_path=file_path)