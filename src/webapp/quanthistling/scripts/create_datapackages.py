#-*- coding: utf8 -*-

# import Python system modules to write files
import sys
import os
import shutil
import glob
import zipfile

# add path to script
sys.path.append(os.path.abspath('.'))

# import pylons and web application modules
import pylons.test
from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from paste.deploy import appconfig


def main(argv):

    if len(argv) < 2:
        print "call: export_tables.py ini_file"
        exit(1)

    ini_file = argv[1]
    
    bibtex_key_param = None
    if len(argv) >= 3:
        bibtex_key_param = argv[2]

    # load web application config
    conf = appconfig('config:' + ini_file, relative_to='.')
    config = None
    if not pylons.test.pylonsapp:
        config = load_environment(conf.global_conf, conf.local_conf)

    # Create database session
    metadata.create_all(bind=Session.bind)

    packages_dir = os.path.join(
        config['pylons.paths']['static_files'], 'downloads', "datapackages")

    subdirs = os.walk(packages_dir).next()[1]

    for subdir in subdirs:
        print("Copying files for {0}...".format(subdir))

        # Copy GrAF files
        from_graf_dir = os.path.join(
            config['pylons.paths']['static_files'], 'downloads', "xml", subdir)
        to_graf_dir = os.path.join(packages_dir, subdir, 'graf')
        if not os.path.exists(to_graf_dir):
            os.makedirs(to_graf_dir)

        src_files = os.listdir(from_graf_dir)
        for file_name in src_files:
            full_file_name = os.path.join(from_graf_dir, file_name)
            if (os.path.isfile(full_file_name)):
                shutil.copy(full_file_name, to_graf_dir)

        # Copy annotation file
        to_scripts_dir = os.path.join(packages_dir, subdir, 'scripts')
        if not os.path.exists(to_scripts_dir):
            os.makedirs(to_scripts_dir)

        annotation_file = os.path.join("scripts", "annotations", "annotations_for_{0}.py".format(subdir))
        print("  " + annotation_file)
        if (os.path.isfile(annotation_file)):
            shutil.copy(annotation_file, to_scripts_dir)

        # Copy manual annotations
        to_annotations_dir = os.path.join(packages_dir, subdir, 'scripts', 'manual_annotations')
        if not os.path.exists(to_annotations_dir):
            os.makedirs(to_annotations_dir)

        from_annotations_dir = os.path.join("scripts", "annotations", "txt", "{0}*.py.txt".format(subdir))
        for f in glob.glob(from_annotations_dir):
            print("  " + f)
            if (os.path.isfile(f)):
                shutil.copy(f, to_annotations_dir)

        # ZIP it
        myzip = zipfile.ZipFile(os.path.join(packages_dir, "{0}.zip".format(subdir)), 'w', zipfile.ZIP_DEFLATED)
        for root, dirnames, files in os.walk(os.path.join(packages_dir, subdir)):
            for f in files:
                myzip.write(os.path.join(root, f), os.path.relpath(os.path.join(root, f), packages_dir))
        myzip.close()





if __name__ == "__main__":
    main(sys.argv)