import torch
import numpy as np

def normalize_tensor(in_feat, eps=1e-10):
    norm_factor = torch.sqrt(torch.sum(in_feat**2, dim=1, keepdim=True))
    return in_feat / (norm_factor + eps)

# Optional stubs to prevent crash (these are only used by DSSIM / L2)
def tensor2np(tensor):
    return tensor.squeeze().permute(1, 2, 0).detach().cpu().numpy()

def tensor2tensorlab(tensor, to_norm=True):
    return tensor  # Stub — not needed unless you're using Lab-space metrics

def dssim(img1, img2, range=255.):
    return np.array([0.0])  # Stub — not used in LPIPS scores

def l2(img1, img2, range=255.):
    return np.array([0.0])  # Stub — not used in LPIPS scores

def tensor2im(tensor):
    return tensor.squeeze().permute(1, 2, 0).detach().cpu().numpy()
