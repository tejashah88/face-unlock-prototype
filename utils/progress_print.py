def progress_print(msg='Doing something'):
    def actual_progress_print(func):
        def wrapper(*args, **kwargs):
            print(f'{msg}...', end='')
            val = func(*args, **kwargs)
            print('done!')
            return val
        return wrapper
    return actual_progress_print