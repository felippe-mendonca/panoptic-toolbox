import os
import sys
import json
import requests
import tarfile
from threading import Thread
from queue import Queue
import logging
import time

calib_file = 'calibration.json'
calib_url = 'http://domedb.perception.cs.cmu.edu/webdata/dataset/{dataset}/calibration_{dataset}.json'
pose3d_vga_file = 'vgaPose3d_stage1.tar'
pose3d_vga_url = 'http://domedb.perception.cs.cmu.edu/webdata/dataset/{dataset}/vgaPose3d_stage1.tar'
pose3d_mpii_file = 'hdPose3d_stage1.tar'
pose3d_mpii_url ='http://domedb.perception.cs.cmu.edu/webdata/dataset/{dataset}/hdPose3d_stage1.tar'
pose3d_coco_file = 'hdPose3d_stage1_coco19.tar'
pose3d_coco_url = 'http://domedb.perception.cs.cmu.edu/webdata/dataset/{dataset}/hdPose3d_stage1_coco19.tar'

log = logging.getLogger(name='__get_poses__')
LOGGING_FMT = '[%(levelname)s][%(thread)d][%(asctime)s] %(message)s'
console = logging.StreamHandler()
log.addHandler(console)
console.setFormatter(logging.Formatter(LOGGING_FMT))
log.setLevel(logging.INFO)

def wget(url, destination_file):
    with requests.get(url, stream=True) as r:
        with open(destination_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
def tar_xf(filename, output_folder, remove_tar=False):
    try:
        tar = tarfile.open(filename)
        tar.extractall(path=output_folder)
        tar.close()
    except:
        log.warn('Failed to extract {}. Invalid file.'.format(filename))
    if remove_tar:
        if os.path.isfile(filename):
            os.remove(filename)


def get_output_folder(base_folder, dataset):
    output_folder = os.path.join(base_folder, dataset)
    try:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
    except:
        pass
    return output_folder

def get_calib(base_folder, dataset):
    out_folder = get_output_folder(base_folder, dataset)
    out_file = os.path.join(out_folder, calib_file)
    if not os.path.exists(out_file):
        url = calib_url.format(dataset=dataset)
        wget(url, out_file)

def get_coco_pose(base_folder, dataset, remove_tar=True):
    out_folder = get_output_folder(base_folder, dataset)
    out_file = os.path.join(out_folder, pose3d_coco_file)
    if not os.path.exists(out_file):
        url = pose3d_coco_url.format(dataset=dataset)
        wget(url, out_file)

def get_mpii_pose(base_folder, dataset, remove_tar=True):
    out_folder = get_output_folder(base_folder, dataset)
    out_file = os.path.join(out_folder, pose3d_mpii_file)
    if not os.path.exists(out_file):
        url = pose3d_mpii_url.format(dataset=dataset)
        wget(url, out_file)

def worker(q):
    while True:
        dl_type, base_folder, dataset = q.get()
        log.info('[START] [{}|{}|{}]'.format(dl_type, base_folder, dataset))
        if dl_type == 'calib':
            get_calib(base_folder, dataset)
        elif dl_type == 'coco_pose':
            get_coco_pose(output_folder, dataset)
        elif dl_type == 'mpii_pose':
            get_mpii_pose(output_folder, dataset)
        else:
            pass
        log.info('[DONE] [{}|{}|{}]'.format(dl_type, base_folder, dataset))
        q.task_done()


n_threads = 10
queue = Queue()
threads = [ Thread(target=worker, args=(queue,)) for _ in range(n_threads)]
for t in threads:
    t.daemon = True
    t.start()

with open('datasets.json', 'r') as f:
    datasets = json.load(f)

output_folder='test/'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

targets = ['calib', 'mpii_pose']
# targets = ['calib', 'coco_pose', 'mpii_pose']
# Download all files
for sequence, seq_datasets in datasets.items():
    for dataset in seq_datasets:
        for target in targets:
            queue.put((target, output_folder, dataset))
queue.join()

# Check files and extract *.tar.gz files
for folder, _, files in os.walk(output_folder):
    if folder == output_folder.strip('/'):
        continue
    for target in targets:
        if target == 'calib':
            if calib_file not in files:
                log.warn('{} not present'.format(os.path.join(folder, calib_file)))
        elif target == 'coco_pose':
            f = os.path.join(folder, pose3d_coco_file)
            if pose3d_coco_file not in files:
                log.warn('{} not present'.format(f))
            else:
                log.info('Extracting {}'.format(f))
                tar_xf(f, folder, remove_tar=True)
        elif target == 'mpii_pose':
            f = os.path.join(folder, pose3d_mpii_file)
            if pose3d_mpii_file not in files:
                log.warn('{} not present'.format(f))
            else:
                log.info('Extracting {}'.format(f))
                tar_xf(f, folder, remove_tar=True)
        else:
            pass
