import glob
import py_compile

files = glob.glob('coinbot/*.py') + glob.glob('airfarm/*.py')
for path in files:
    py_compile.compile(path, doraise=True)
print('OK', len(files), 'files compiled')
