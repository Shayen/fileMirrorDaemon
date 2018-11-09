_version__ = '0.9'

import sys
import os
import filecmp
import shutil
import logging
import logging.handlers
import traceback
import time
import inspect

from src import daemon
from src import reader

def _setFilePathOnLogger(logger, path):
	# Remove any previous handler.
	_removeHandlersFromLogger(logger, logging.handlers.TimedRotatingFileHandler)

	# Add the file handler
	handler = logging.handlers.TimedRotatingFileHandler(path, 'midnight', backupCount=10)
	handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
	logger.addHandler(handler)

def _removeHandlersFromLogger(logger, handlerTypes=None):
	"""
	Remove all handlers or handlers of a specified type from a logger.
	@param logger: The logger who's handlers should be processed.
	@type logger: A logging.Logger object
	@param handlerTypes: A type of handler or list/tuple of types of handlers
		that should be removed from the logger. If I{None}, all handlers are
		removed.
	@type handlerTypes: L{None}, a logging.Handler subclass or
		I{list}/I{tuple} of logging.Handler subclasses.
	"""
	for handler in logger.handlers:
		if handlerTypes is None or isinstance(handler, handlerTypes):
			logger.removeHandler(handler)

class Config(object):

	print "current location :", __file__

	def __init__(self):
		currentPath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
		example_config_path = "%s/%s"%(currentPath, 'example_config.yml')
		config_path = "%s/%s"%(currentPath, 'config.yml')

		if not os.path.exists(config_path):
			shutil.copy2(example_config_path, config_path)

		self._configData = reader.read(config_path)

	@property
	def PIDFile(self):
		return self._configData['pidFile']

	@property
	def source(self):
		return self._configData['source']

	@property
	def destination(self):
		return self._configData['destination']

	@property
	def logPath(self):
		return self._configData['logPath']

	@property
	def logFile(self):
		return self._configData['logFile']

	@property
	def logLevel(self):
		return int(self._configData['logLevel'])

	@property
	def logMode(self):
		return int(self._configData['logMode'])

	@property
	def gitRepo(self):
		return self._configData['gitRepo']

	@property
	def fetch_interval(self):
		return int(self._configData['fetch_interval'])

	@property
	def IGNORE_dir(self):
		result = self._configData.get('IGNORE_dir', [])
		return  result if type(result) == type(dict()) else list(result)

	@property
	def IGNORE_fileType(self):
		result = self._configData.get('IGNORE_fileType', [])
		return result if type(result) == type(dict()) else list(result)

	def getLogFile(self, filename=None):

		if filename is None:
			if self.logFile:
				filename = self.logFile
			else:
				raise IOError('The config file has no logFile option.')

		path = self.logPath
		if path:

			if not os.path.exists(path):
				os.makedirs(path)
			elif not os.path.isdir(path):
				raise IOError('The logPath value in the config should point to a directory.')

			path = os.path.join(path, filename)
		else :
			path = filename

			return path

class Engine(object):

	def __init__(self):
		self._continue = True
		self.config = Config()

		# Setup the logger for the main engine
		if self.config.logMode == 0:
			# Set the root logger for file output.
			rootLogger = logging.getLogger()
			# rootLogger.setLevel(self.config.logLevel)
			_setFilePathOnLogger(rootLogger, self.config.getLogFile())
			print 'Log file :', self.config.getLogFile()

			# Set the engine logger for email output.
			self.log = logging.getLogger('engine')
			# self.setEmailsOnLogger(self.log, True)
		else:
			# Set the engine logger for file and email output.
			self.log = logging.getLogger('engine')
			self.log.config = self.config
			_setFilePathOnLogger(self.log, self.config.getLogFile())
			# self.setEmailsOnLogger(self.log, True)

		self.log.setLevel(self.config.logLevel)

		super(Engine, self).__init__()

	def _get_diff_files(self, source, dest, IGNORE_dir=[], IGNORE_fileType=[]):

		source = source.replace('\\', '/')
		dest = dest.replace('\\', '/')

		# List files
		s_files = walkingDir(source, IGNORE_dir=IGNORE_dir, IGNORE_fileType=IGNORE_fileType)
		d_files = walkingDir(dest, IGNORE_dir=IGNORE_dir, IGNORE_fileType=IGNORE_fileType) if os.path.exists(
			dest) else []

		# Get relative source file
		rel_source = []
		for f_id in range(len(s_files)):
			rel_source.append(s_files[f_id].replace('\\', '/').replace(source, ''))

		# Get relative destination file
		rel_dest = []
		for f_id in range(len(d_files)):
			rel_dest.append(d_files[f_id].replace('\\', '/').replace(dest, ''))

		# Compare file
		need2add = []
		need2remove = []
		# Find file for copy to destination
		for rel_s_file in rel_source:
			s_file = source + rel_s_file
			d_file = dest + rel_s_file

			cmp_result = False
			if rel_s_file in rel_dest:
				cmp_result = filecmp.cmp(s_file, d_file, shallow=True)

			if not cmp_result:
				# Copy file
				if not os.path.exists(os.path.dirname(d_file)):
					os.makedirs(os.path.dirname(d_file))

				# print "Copy :", s_file, ">", d_file
				need2add.append((s_file, d_file))

		# Find file that need to remove from destination
		for rel_d_file in rel_dest:
			# s_file = source + rel_d_file
			d_file = dest + rel_d_file

			if rel_d_file not in rel_source:
				need2remove.append(d_file)

		print "compare finished"
		return need2add, need2remove

	def _mirror(self):

		self.log.debug("Getting difference files ...")

		need2add, need2remove = self._get_diff_files(self.config.source, self.config.destination,
								                     IGNORE_dir=self.config.IGNORE_dir,
								                     IGNORE_fileType=self.config.IGNORE_fileType)

		if need2add == [] and need2remove == [] :
			self.log.debug("Files is indenticald.")
		else:
			for _s, _d in need2add:
				self.log.debug("Copy : %s -> %s"%(_s,_d))
				shutil.copy2(_s, _d)

			for _f in need2remove :
				self.log.debug("Remove : %s"%(_f))
				os.remove(_f)

			self.log.debug("Mirror success.")

	def start(self):
		try:
			self._mainLoop()
		except KeyboardInterrupt:
			self.log.warning('Keyboard interrupt. Cleaning up...')
		except Exception, err:
			msg = 'Crash!!!!! Unexpected error (%s) in main loop.\n\n%s'
			self.log.critical(msg, type(err), traceback.format_exc(err))

	def stop(self):
		self._continue = False

	def _mainLoop(self):
		self.log.debug("Main loop started.")
		while self._continue:
			self._mirror()
			time.sleep(self.config.fetch_interval)

		self.log.debug('Shuting down processing loop.')

class LinuxDaemon(daemon.Daemon):

	def __init__(self):
		self._engine = Engine()
		super(LinuxDaemon, self).__init__( serviceName= 'fileMirror',pidfile = self._engine.config.PIDFile)

	def start(self, daemonize=True):

		if not daemonize:
			# Setup the stdout logger
			handler = logging.StreamHandler()
			handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
			logging.getLogger().addHandler(handler)

		super(LinuxDaemon, self).start(daemonize)

	def _run(self):
		self._engine.start()

	def _cleanup(self):
		self._engine.stop()

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

def main ():

	if sys.platform not in ("linux", "linux2"):
		print "Support only Linux."
		return 2

	action = None

	if len(sys.argv) > 1:
		action = sys.argv[1]

	if action:
		daemon = LinuxDaemon()
		func = getattr(daemon, action, None)
		if action[:1] != '_' and func != None :
			func()
			return 0

	print "usage: %s start|stop|restart|foreground" % sys.argv[0]
	return 2

# source = "/mnt/META/SCRIPTS/MEME"
	# dest = os.environ['HOME']+'/META/SCRIPTS/MEME'
	# need2add, need2remove = get_diff_files(source, dest,IGNORE_dir=[".idea", 'USER_ACTIVITY'], IGNORE_fileType = ['.pyc'])
	#
	# print "Need to add"
	# for i in need2add :
	# 	# print '\t' , i[0], '>', i[1]
	# 	print ( '\t' + i[0] + '>'+ i[1])
	# 	shutil.copy2(i[0], i[1])
	#
	# print "Need to remove"
	# for j in need2remove :
	# 	print '\t' , j
	# 	os.remove(j)

if __name__ == '__main__':
	sys.exit(main())
	# import tqdm, time
	#
	# for i in tqdm.tqdm(range(10)):
	# 	time.sleep(0.2)

