from pathlib import Path
import os,sys,json,tempfile
BASE=Path(__file__).resolve().parent
runtime=BASE/'.runtime';runtime.mkdir(exist_ok=True)
os.environ['TEMP']=os.environ['TMP']=str(runtime)
tempfile.tempdir=str(runtime)
os.environ['JUPYTER_RUNTIME_DIR']=str(runtime)
os.environ['IPYTHONDIR']=str(runtime/'ipython')
os.environ['MPLCONFIGDIR']=str(runtime/'matplotlib')
kernels=BASE/'.jupyter/kernels/mdp-analysis';kernels.mkdir(parents=True,exist_ok=True)
python=BASE/'.venv/Scripts/python.exe'
(kernels/'kernel.json').write_text(json.dumps({'argv':[str(python),'-m','ipykernel_launcher','-f','{connection_file}'],
 'display_name':'Python (MDP analyse)','language':'python'}),encoding='utf-8')
os.environ['JUPYTER_PATH']=str(BASE/'.jupyter')
import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter
for name in sys.argv[1:] or ['01_geopandas_belgie.ipynb','02_analyse_presentatie.ipynb']:
    print('EXECUTE',name,flush=True)
    nb=nbformat.read(BASE/name,as_version=4)
    nb.metadata.kernelspec={'display_name':'Python (MDP analyse)','language':'python','name':'mdp-analysis'}
    client=NotebookClient(nb,timeout=600,kernel_name='mdp-analysis',resources={'metadata':{'path':str(BASE)}},
        on_cell_executed=lambda cell,cell_index,**kwargs: print('  cell',cell_index,'done',flush=True))
    client.execute()
    nbformat.validate(nb); nbformat.write(nb,BASE/name)
    # HTML export happens after notebook validation with the available Jupyter templates.
    print('PASS',name,len([c for c in nb.cells if c.cell_type=='code']),'code cells',flush=True)

