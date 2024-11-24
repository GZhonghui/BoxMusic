import dropbox, vlc, os

def main():
    token = ''
    dbx = dropbox.Dropbox(token)

    for entry in dbx.files_list_folder('').entries:
        print(entry.name)

    path = '/王菲/你王菲所以我王菲/王菲 - 守望麦田.flac'
    try:
        md, res = dbx.files_download(path)
    except dropbox.exceptions.HttpError as err:
        print('*** HTTP error', err)
        return None
    data = res.content
    print(len(data), 'bytes; md:', md)
    with open('out.flac', 'wb') as file:
        file.write(data)

if __name__ == '__main__':
    main()