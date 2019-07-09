import torch as th
import torch.nn as nn
import numpy as np
from torchvision.utils import save_image
from torch.utils.data import DataLoader
from loader import RotDataset
from time import ctime
from sacred import Experiment

def validate(params, test_loader, _log):
    with th.no_grad():
        sig = nn.Sigmoid()
        shape = params['shape']
        res = th.zeros(shape)
        pad = params['pad']
        model = th.load(params['load_model'])
        _log.info('[{}] model is successfully loaded.'.format(ctime()))
        test_iter = iter(test_loader)
        for iter_ in range(len(test_iter)):
            sample = test_iter.next()
            data, gt = sample['data'].cuda(), sample['gt'].cuda()
            ignore = gt < 0
            prds = sig(model.forward(data))[:, :, pad:-pad, pad:-pad]
            prds[ignore] = 0
            del data, gt, ignore
            for idx in range(prds.shape[0]):
                row, col = sample['index'][0][idx], sample['index'][1][idx]
                res[row*params['ws']:(row+1)*params['ws'], col*params['ws']:(col+1)*params['ws']] = prds[idx, 0, :, :]
            _log.info('[{}]: writing [{}/{}]'.format(ctime(), iter_, len(test_iter)))
        _log.info('all images are written!')
        save_image(res, '{}{}_predictions.tif'.format(params['save_to'], params['flag']))
        np.save('{}{}_predictions.npy'.format(params['save_to'], params['flag']), res.data.numpy())

ex = Experiment('validate_rotation')

@ex.config
def ex_cfg():
    params = {
        'data_path': '/dev/shm/rotated_dataset.h5',
        'load_model': '',
        'save_to': 'runs/result/',
        'region': 'Veneto',
        'ws': 400,
        'pad': 64,
        'shape': (4201, 19250),
        'flag': 'test',
        'bs': 5,
        'n_workers': 4
    }

@ex.automain
def main(params, _log):
    vd = RotDataset(params['data_path'], params['region'], 'test')
    vd_loader = DataLoader(vd, batch_size=params['bs'], num_workers=params['n_workers'])
    _log.info('[{}] prepared the dataset for validation.'.format(ctime()))
    validate(params, vd_loader, _log)