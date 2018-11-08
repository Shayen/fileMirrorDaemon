import os
import filecmp
import core
import shutil

def get_diff_files(source, dest, IGNORE_dir=[], IGNORE_fileType = []):
	source = source.replace('\\', '/')
	dest   = dest.replace('\\', '/')

	# List files
	s_files = core.walkingDir(source,IGNORE_dir=IGNORE_dir, IGNORE_fileType = IGNORE_fileType)
	d_files = core.walkingDir(dest, IGNORE_dir=IGNORE_dir, IGNORE_fileType = IGNORE_fileType)

	# Get relative source file
	rel_source = []
	for f_id in range(len(s_files)):
		rel_source.append(s_files[f_id].replace('\\', '/').replace(source, ''))

	# Get relative destination file
	rel_dest = []
	for f_id in range(len(d_files)) :
		rel_dest.append( d_files[f_id].replace('\\', '/').replace(dest, '') )

	# Compare file
	need2add = []
	need2remove = []
	# Find file for copy to destination
	for rel_s_file in rel_source:
		s_file = source + rel_s_file
		d_file = dest + rel_s_file

		cmp_result = False
		if rel_s_file in rel_dest :
			cmp_result = filecmp.cmp(s_file, d_file, shallow=True)

		if not cmp_result :
			# Copy file
			if not os.path.exists(os.path.dirname(d_file)) :
				os.makedirs(os.path.dirname(d_file))

			# print "Copy :", s_file, ">", d_file
			need2add.append((s_file, d_file))

	# Find file that need to remove from destination
	for rel_d_file in rel_dest:
		# s_file = source + rel_d_file
		d_file = dest + rel_d_file

		if rel_d_file not in rel_source:
			print rel_d_file, d_file
			need2remove.append(d_file)

	return need2add, need2remove

def main ():
	source = "H:/programming/Python/fileMirrorDaemon"
	dest = 'C:/Users/siras/Downloads/dest/fileMirrorDaemon'
	need2add, need2remove = get_diff_files(source, dest,IGNORE_dir=[".idea"], IGNORE_fileType = ['.pyc'])

	print "Need to add"
	for i in need2add :
		print '\t' , i[0], '>', i[1]

	print "Need to remove"
	for j in need2remove :
		print '\t' , j

if __name__ == '__main__':
	main()