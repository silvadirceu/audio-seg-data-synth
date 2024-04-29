import logging, logging.handlers
import os
import pathlib
# print(str(pathlib.Path(__file__).parent.parent.parent.absolute()) + "/log/worker.log")

import logging, logging.handlers
import os

def get_logger(module_name):
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s:%(levelname)s : %(message)s')
    file_location = "/log/logger.log"

    try:
        if not os.path.exists(file_location):
            os.makedirs("/log")
            f= open(file_location,"w+")
            f.close()
    except:
        pass
    

    file_handler = logging.FileHandler(file_location)
    file_handler.setFormatter(formatter)

    if (logger.hasHandlers()):
        logger.handlers.clear()
    logger.addHandler(file_handler)
    return ({'logger':logger, 'path':file_location})



if __name__ == '__main__':
    handler = get_logger(__name__)
    logger = handler['logger']
    print(handler['path'])
    logger.info("working")
    
