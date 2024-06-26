import os
import random
import numpy as np
import torch
import torch.utils.data as data_utils
import torchvision.transforms as transforms

from PIL import Image
from torch.utils.data import Dataset


class DatasetFromSubset(Dataset):
    def __init__(self, subset, transform=None):
        self.subset = subset
        self.transform = transform

    def __getitem__(self, index):
        x, y = self.subset[index]
        if self.transform:
            x = self.transform(x)
        return x, y

    def __len__(self):
        return len(self.subset)


class COAD(data_utils.Dataset):
    ''' Unlabeled Dataset Class'''
    def __init__(
        self,
        data_path,
        exclude=None,
        mode='20.0',
        limit=float("inf"),
        transform=None
    ):
        super().__init__()
        assert mode in ['40.0', '20.0', '10.0', '5.0']

        self.data_path = data_path
        self.indexed_foldername = []
        self.indexed_filename = []

        if transform is not None:
            self.transform = transform
        else:
            self.transform = transforms.Compose([transforms.ToTensor()])

        if exclude is not None:
            patient_id = [file_name.split('-')[2] for file_name in exclude]
        else:
            patient_id = []

        i = 0
        for folder in os.listdir(data_path):
            i += 1
            if i < limit and folder[-5:] == 'files':
                folder = folder + '/' + mode
                patch_path = os.path.join(data_path, folder)
                if os.path.isdir(patch_path):
                    for file in os.listdir(patch_path):
                        if folder.split('-')[2] not in patient_id:
                            self.indexed_foldername.append(folder)
                            self.indexed_filename.append(file)

    def __len__(self):
        i = 0
        for file in self.indexed_filename:
            i += 1
        return i

    def __getitem__(self, idx):
        image_filepath = self.data_path + '/' + self.indexed_foldername[
            idx] + '/' + self.indexed_filename[idx]
        image = Image.open(image_filepath)
        image = self.transform(image)
        label = 0
        return image, label


def make_dataset(dataset, images_per_class=5):
    labeled_indices = []

    # randomly sample labeled indices
    for i in range(0, 9):
        indices = random.sample(
            np.where(np.array(dataset.targets) == i)[0].tolist(),
            images_per_class
        )
        labeled_indices = labeled_indices + indices

    # recover the corresponding labels
    labeled_targets = [dataset.targets[i] for i in labeled_indices]

    # create the labeled subset
    labeled_dataset = torch.utils.data.Subset(dataset, labeled_indices)
    labeled_dataset = DatasetFromSubset(labeled_dataset, transform=None)

    # length of original dataset
    total_indices = list(range(0, 100000))

    # indices of unlabeled dataset
    unlabeled_indices = [
        index for index in total_indices if index not in labeled_indices
    ]

    # create the unlabeled subset
    unlabeled_dataset = torch.utils.data.Subset(dataset, unlabeled_indices)
    unlabeled_dataset = DatasetFromSubset(unlabeled_dataset, transform=None)

    return labeled_targets, labeled_dataset, unlabeled_dataset
