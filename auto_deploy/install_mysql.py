#!python
# -*- coding:utf-8 -*-

import os, sys
import zipfile

def extract_zip(para_list):
    if len(para_list) > 1:
        package, setup_dir = para_list[0], para_list[1]
    if not os.path.isdir(setup_dir):
        try:
            os.makedirs(setup_dir)
        except Exception as e:
            print("cannot create target directory:", setup_dir)
            return 1
    f = zipfile.ZipFile(package, 'r')
    try:
        for file in f.namelist():
            f.extract(file, setup_dir)
    except Exception as e:
        print("error extract package:",package)
        return 2
    print(package, " extract to ", setup_dir, "successful.\n\n")
    return 0

def mysql_install(para_list):
    if len(para_list) > 1:
        package, setup_dir = para_list[0], para_list[1]
    global mysql_install_dir
    mysql_install_dir = setup_dir
    extract_zip(para_list)
    
def init_srv(para_list):
    '''
    register mysql service with 'srv_name' and default ini 'cfg_file'
    '''
    if not mysql_install_dir:
        print("not found mysql install directory,install first")
        return
    if len(para_list) > 1:
        srv_name, cfg_file = para_list[0], para_list[1]
    else:
        srv_name = para_list[0]
        cfg_file = fileloc(mysql_install_dir, "my-default.ini")
    if not os.path.isfile(cfg_file):
        print("mysql config file not found: ", cfg_file)
        return
    try:
        sqld = fileloc(mysql_install_dir, "mysqld.exe")
        cmd_reg = sqld + " --install " + srv_name + " --defaults-file=" + cfg_file
        print(cmd_reg)
        rtn = os.system(cmd_reg)
        if not rtn:
            print("register mysql service with service name:",srv_name)
            rtn_srv = os.system("net start " +srv_name)
            if rtn:
                return 1
    except Exception as e:
        print("try to register mysql service yourself:", e)

def init_mysql(para_list):
    schema = 'root'
    if len(para_list) > 1:
        sql_dir, schema = para_list[0], para_list[1]
    mysqlexe = fileloc(mysql_install_dir, 'mysql.exe')
    try:
        for path, subdir, file in (os.walk(sql_dir)):
            for f in file:
                if f.endswith('sql'):
                    fullname = os.path.join(path, f)
                    cmd = mysqlexe + " -u " + schema  + " <" + fullname
                    rtn = os.system(cmd)
                    if not rtn:
                        print("run ", sql_dir, "sql files successful")
    except Exception as e:
        print("failed exec create_db sql")

def odbc_setup():
    pass


def fileloc(target_dir, file):
    for path, subpath, files in (os.walk(target_dir)):
        for f in files:
            if f == file:
                return os.path.join(path, f)
                
def get_para(para_name_list):
    '''
     根据提示列表，获取相应输入值列表
    '''
    para = []
    for v in para_name_list:
        answer = input(v + "=")
        if answer:
            para.append(answer)
    return para
    

def cmd_menu():
    
    menu = {}   #菜单调用
    menu['1'] = [ mysql_install, 'zip包名', '安装目录']  
    menu['2'] = [ init_srv, 'mysql服务名', '配置文件地址']
    menu['3'] = [ init_mysql, '脚本路径', '执行schema']
    menu['4'] = [ init_mysql, '脚本路径', '执行schema']
    menu['5'] = [ init_mysql, '脚本路径']
    menu['6'] = [ odbc_setup, 'odbc包名', '安装路径']
    
    
    while True:
        print("1. zip包安装")
        print("2. 初始化mysql服务")
        print("2. 数据库及用户 exec as root")        #需脚本路径
        print("3. 数据库初始化 exec as schema")      #需脚本路径 和 schema名
        print("4. schema密码初始化")
        print("5. odbc 配置")
        

        
        choice = input("please select choice: ")
        
        if choice.upper() == 'X':
            break
        elif choice in menu.keys():
            menu[choice][0](get_para(menu[choice][1:]))
        else:
            continue
            
if __name__ == '__main__':
    mysql_install_dir = 'c:\\mysql5'
    cmd_menu()