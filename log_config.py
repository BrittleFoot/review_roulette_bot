from os import path


log_folder = path.dirname(__file__) + '/logs/'

config = {

    'system': {
        'format': '[%(asctime)-15s] [%(levelname)7s] [%(module)16s:%(lineno)-3d] %(message)s',

        'info_filename': log_folder + 'system.log',
        'debug_filename': log_folder + 'system-debug.log'
    }

}
