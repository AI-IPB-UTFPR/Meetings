import json
import sys
import os
import shutil
import threading
import urllib.request
import magic

if len(sys.argv) < 2:
    print("Invalid arguments: <file> <folder> <[list of error ids]>")
    exit()
os.mkdir(sys.argv[2])
jfile = json.load(open(sys.argv[1]))
imgs = jfile['images']
ann = jfile['annotations']
sem = threading.Semaphore()
semdir = threading.Semaphore()
error = []
chunk = 1
CHUNK_SIZE = 101

def get_chunk():
    sem.acquire()
    global chunk
    if chunk >= len(imgs):
        sem.release()
        return False
    else:
        ret = chunk
        chunk += CHUNK_SIZE
        sem.release()
        print(ret)
        return ret

def create_dir(directory):
    sem.acquire()
    if not os.path.exists(directory):
        os.mkdir(directory)
    sem.release()

def request():
    init = get_chunk()
    while init:
        final = init + CHUNK_SIZE
        if final > len(imgs):
            final = len(imgs)+1
        for idx in range(init, final):
            if imgs[idx]['image_id'] == ann[idx]['image_id']:
                create_dir(sys.argv[2]+'/'+str(ann[idx]['label_id']))
                try:
                    fname, header = urllib.request.urlretrieve(imgs[idx]['url'][0])
                    #ftype = header['Content-Type'].split("/")[-1]
                    ftype = magic.from_file(fname, mime=True)
                    ftype = ftype.split("/")[-1]
                    
                    shutil.move(fname, sys.argv[2]+'/'+str(ann[idx]['label_id'])+'/'+str(ann[idx]['image_id'])+'.'+ftype)
                    print(ann[idx]['image_id'], "OK")
                except Exception as e:
                    print(ann[idx]['image_id'], 'ERROR', e)
                    error.append(ann[idx]['image_id'])
            else:
                print("error in index: ", idx)
                exit()
        init = get_chunk()

threads = []

for i in range(0,100):
    t = threading.Thread(target=request)
    threads.append(t)
    t.start()
for t in threads:
    t.join()

print("Copy the errors id's: ", error)
