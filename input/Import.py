'''
Created on Mar 29, 2013

@author: Behrooz Afghahi
@version: 0.1
@see: /docs/API/Input.Importer.txt
'''

import os, threading
import subprocess
from sys import stdout

import iTunes, Filesystem
import config
from data.DB_Helper import DB_Helper

class Importer(object):
    '''
    Imports the library in the background
    '''
    
    __daemon = None

    def __init__(self, path, max_files = 100000):
        '''
        Tries to detect library type and import it
        '''
        
        if os.path.isfile(path): # is the a file ?
            if os.path.splitext(path)[1].lower() == "xml": # iTunes ?
                lib = iTunes.Input(max_files)
                self.__files = lib.Import({"xml_path": path})
            else: # probably a music file
                self.__files = [path]
        else: # a directory, import all music files
            lib = Filesystem.Input(max_files)
            self.__files = lib.Import({"path":path})
        
        if self.__files is False: # importing failed, no files, or permission
            self.__files = []
            
    def startDaemon(self):
        '''
        Starts the daemon process
        '''
        self.__daemon = FetchData(self.fetcher)
        self.__daemon.start()
        
    def fetcher(self):
        '''
        This is called to fetch song data
        '''
        
        if config.CHOSEN_FEATURE_TABLE == config.DEFAULT_SONG_TABLE:
            from data_mining import song_attributes, set_api_key
            set_api_key()
        else:
            from marsyas_mir import song_attributes

        # print the number of files, used to create progress bar
        print (str(len(self.__files)))
        stdout.flush()
        
        db = DB_Helper(True) # create a new database instance
        
        for song in self.__files:
            if not os.path.exists(FetchData.pid_file): # do we have a pid file ?
                return
            
            song_attributes(song, False, db)

            print("#") # print a # for each file that is completed
            try:
                stdout.flush() # flush to have live output in the other process
            except Exception:
                pass
            
        if os.path.exists(FetchData.pid_file): #remove the pid
            os.remove(FetchData.pid_file)
    
    def isAlive(self):
        '''
        Check to see if the damon is alive (maybe killed or the job is finished)
        '''
        return self.__daemon.isAlive()
    
    def join(self):
        '''
        Wait until the damon is finished.
        '''
        self.__daemon.join()

class FetchData(threading.Thread):
    '''
    Implements the Thread class to create a daemon
    '''
    pid_file = '.pid'
    
    def __init__(self, fetcher_function = None):
        '''
        Constructor
        '''
        threading.Thread.__init__(self)
        
        if fetcher_function is None:
            self.runnable = self.subprocess
        else:
            self.runnable = fetcher_function
        
        self.daemon = True
        
    def run(self):
        '''
        Call the provided runnable function
        '''
        if os.path.exists(self.pid_file):
            return False
        
        # create a pid file with dummy content
        pid = open(self.pid_file, 'w+')
        pid.write('dummy')
        pid.close()
            
        self.runnable()
    
    def subprocess(self):
        '''
        Runs ./importer.py and updates the progress
        '''
        self.process = {"total":0, "done":0}
        proc = subprocess.Popen(['python', './importer.py', config.CHOSEN_FEATURE_TABLE],
                                stdout=subprocess.PIPE, bufsize=1)
        
        while True:
            line = proc.stdout.readline().strip()
            if not line:
                break
            
            if line == "#":
                self.process["done"] += 1
            else:
                self.process["total"] = int(line)

    @staticmethod
    def removePID():
        try:
            os.remove(FetchData.pid_file)
        except Exception:
            pass