from datetime import datetime

def out(message: str):
    current_time = datetime.now()
    print(f'[{current_time.strftime("%H:%M:%S")}] {message}')

if __name__ == '__main__':
    pass