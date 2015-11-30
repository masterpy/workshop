#!python
# -*- coding:utf-8 -*-

import os, sys
import zipfile

def extract_zip(package, target_dir):
    if not os.path.isdir(target_dir):
        try:
            os.makedirs(target_dir)
        except Exception as e:
            print("cannot create target directory:", target_dir)
            return 1
            
    f = zipfile.ZipFile(package, 'r')
    try:
        for file in f.namelist():
            f.extract(file, target_dir)
        return 0
    except Exception as e:
        print("error extract package:",package)
        return 2

def fileloc(target_dir, exe):
    for path, subpath, file in (os.walk(target_dir)):
        for f in file:
            if f == exe:
                return os.path.join(path, f)
    
    
if __name__ == '__main__':
    dir_name = os.path.dirname(os.path.abspath(__file__))
    if not len(sys.argv) >=3:
        print("useage:")
        print("python install.py package_zip  install_dir  [mysql_srv]")
        exit()
        
    (file, package, install_dir, *srv)  = sys.argv
    
    if os.path.isfile(os.path.join(package)):
        #rtn = extract_zip(package, install_dir)
        rtn = 0
        if rtn:
            print("extract failed:",rtn) 
            exit()
        else:
            print("extract successful")
    
    if srv[0]:
        try:
            sqld = fileloc(install_dir, "mysqld.exe")
            default_ini = fileloc(install_dir, "my-default.ini")
            if default_ini:
                cmd_reg = sqld + " --install " + srv[0] + " --defaults-file=" + default_ini
                rtn = os.system(cmd_reg)
                if not rtn:
                    print("register mysql service with name:",srv[0])
        except Exception as e:
            print("try to register mysql service yourself:", e)
        
    