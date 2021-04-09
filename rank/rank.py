#
# rank ds ChRIS plugin app
#
# (c) 2021 Fetal-Neonatal Neuroimaging & Developmental Science Center
#                   Boston Children's Hospital
#
#              http://childrenshospital.org/FNNDSC/
#                        dev@babyMRI.org
#

from chrisapp.base import ChrisApp
import os
import json
from collections import OrderedDict
from functools import cmp_to_key

Gstr_title = r"""

Generate a title from 
http://patorjk.com/software/taag/#p=display&f=Doom&t=rank

"""

Gstr_synopsis = """

(Edit this in-line help for app specifics. At a minimum, the 
flags below are supported -- in the case of DS apps, both
positional arguments <inputDir> and <outputDir>; for FS and TS apps
only <outputDir> -- and similarly for <in> <out> directories
where necessary.)

    NAME

       rank.py 

    SYNOPSIS

        python rank.py                                         \\
            [-h] [--help]                                               \\
            [--json]                                                    \\
            [--man]                                                     \\
            [--meta]                                                    \\
            [--savejson <DIR>]                                          \\
            [-v <level>] [--verbosity <level>]                          \\
            [--version]                                                 \\
            <inputDir>                                                  \\
            <outputDir> 

    BRIEF EXAMPLE

        * Bare bones execution

            docker run --rm -u $(id -u)                             \
                -v $(pwd)/in:/incoming -v $(pwd)/out:/outgoing      \
                fnndsc/pl-rank rank                        \
                /incoming /outgoing

    DESCRIPTION

        `rank.py` ...

    ARGS

        [-h] [--help]
        If specified, show help message and exit.
        
        [--json]
        If specified, show json representation of app and exit.
        
        [--man]
        If specified, print (this) man page and exit.

        [--meta]
        If specified, print plugin meta data and exit.
        
        [--savejson <DIR>] 
        If specified, save json representation file to DIR and exit. 
        
        [-v <level>] [--verbosity <level>]
        Verbosity level for app. Not used currently.
        
        [--version]
        If specified, print version number and exit. 
"""


class Rank(ChrisApp):
    """
    An app to ...
    """
    PACKAGE                 = __package__
    TITLE                   = 'A ChRIS plugin app'
    CATEGORY                = ''
    TYPE                    = 'ds'
    ICON                    = ''   # url of an icon image
    MIN_NUMBER_OF_WORKERS   = 1    # Override with the minimum number of workers as int
    MAX_NUMBER_OF_WORKERS   = 1    # Override with the maximum number of workers as int
    MIN_CPU_LIMIT           = 1000 # Override with millicore value as int (1000 millicores == 1 CPU core)
    MIN_MEMORY_LIMIT        = 200  # Override with memory MegaByte (MB) limit as int
    MIN_GPU_LIMIT           = 0    # Override with the minimum number of GPUs as int
    MAX_GPU_LIMIT           = 0    # Override with the maximum number of GPUs as int

    # Use this dictionary structure to provide key-value output descriptive information
    # that may be useful for the next downstream plugin. For example:
    #
    # {
    #   "finalOutputFile":  "final/file.out",
    #   "viewer":           "genericTextViewer",
    # }
    #
    # The above dictionary is saved when plugin is called with a ``--saveoutputmeta``
    # flag. Note also that all file paths are relative to the system specified
    # output directory.
    OUTPUT_META_DICT = {}

    def define_parameters(self):
        """
        Define the CLI arguments accepted by this plugin app.
        Use self.add_argument to specify a new app argument.
        """

    def run(self, options):
        """
        Define the code to be run by this plugin app.
        """
        folders = os.listdir(options.inputdir)
        severity_files = []
        safe_files = []
        prediction_filename = 'prediction-default.json'
        predictions = {}
        print(folders)
        for folder in folders:
            if os.path.isdir(folder):
                continue
            prediction_path = os.path.join(options.inputdir, folder, prediction_filename)
            if not os.path.exists(prediction_path):
                continue
            f = open(prediction_path, 'r')
            prediction = json.load(f)
            f.close()
            predictions[folder] = prediction
            prediction['instance_id'] = folder

            if prediction['prediction'] == 'COVID-19':
                severity_filename = os.path.join(options.inputdir, folder, 'severity.json')
                f = open(severity_filename, 'r')
                severity = json.load(f)
                f.close()
                prediction['severity'] = severity
        from pprint import pprint


        predictions_list = list(predictions.values())
        def compare(instance_a, instance_b):
            a_type = instance_a['prediction']
            b_type = instance_b['prediction']
            t = ''
            t += a_type[0].upper()
            t += a_type[1:]
            a_type = t
            t = ''
            t += b_type[0].upper()
            t += b_type[1:]
            b_type = t
            if a_type == b_type:
                if a_type == 'COVID-19':
                    severity_a = instance_a['severity']['Geographic severity'] + instance_a['severity']['Opacity severity']
                    severity_b = instance_b['severity']['Geographic severity'] + instance_b['severity']['Opacity severity']
                    value_cmp_a = severity_a
                    value_cmp_b = severity_b
                else:   
                    value_cmp_a = instance_a[a_type]
                    value_cmp_b = instance_b[b_type]
                if value_cmp_a < value_cmp_b:
                    return 1
                return -1


            if a_type == 'COVID-19':
                return -1

            if b_type == 'COVID-19':
                return 1

            if a_type == 'Pneumonia':
                return -1

            if b_type == 'Pneumonia':
                return 1
            return -1
        ranking = sorted(predictions_list, key=cmp_to_key(compare))
        # pprint(ranking)

        # clear outpath 
        os.system('rm -rf %s/*' % options.outputdir)
        # output
        with open(options.outputdir + "/0000-ranking_result.json", "w") as f:
            json.dump(ranking,f,indent=6)
        import shutil 
        counter=0
        for patient in ranking:
            # pprint (file['instance_id'])
            counter += 1
            # src = 'options.inputdir/'+ patient['instance_id']
            # dest= 'options.outputdir/'+str(counter)+'/'+patient['instance_id']
            src = os.path.join(options.inputdir, patient['instance_id']) 
            dest= os.path.join(options.outputdir, '%04d-%s' % (counter, patient['instance_id'])) 
            shutil.copytree(src, dest)
    def show_man_page(self):
        """
        Print the app's man page.
        """
        print(Gstr_synopsis)
