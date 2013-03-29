'''
Created on Mar 29, 2013

@author: Behrooz Afghahi
@version: 0.1
'''

import os, threading
import iTunes, Filesystem

class Importer(object):
    '''
    Imports the library in the background
    '''
    
    __daemon = None

    def __init__(self, path, max_files = 100):
        '''
        Tries to detect library type and import it
        '''
        
        if os.path.isfile(path):
            if os.path.splitext(path)[1].lower() == "xml":
                lib = iTunes.Input(max_files)
                self.__files = lib.Import({"xml_path": path})
            else:
                self.__files = [path]
        else:
            lib = Filesystem.Input(max_files)
            self.__files = lib.Import({"path":path})
        
        if self.__files is False:
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
        # do some stuff
        self.__files
    
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
    def __init__(self, fetcher_function):
        '''
        Constructor
        '''
        threading.Thread.__init__(self)
        
        self.runnable = fetcher_function
        
        self.daemon = True
        
    def run(self):
        '''
        Call the provided runnable function
        '''
        self.runnable()