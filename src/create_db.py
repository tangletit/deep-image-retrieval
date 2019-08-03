from tqdm import tqdm
import torch
import gc
import os
import numpy as np
from sklearn.metrics import cohen_kappa_score
from model import TripletLoss, TripletNet, Identity
from dataset import QueryExtractor, EvalDataset
from torchvision import transforms
import torchvision.models as models
from torch.utils.data import DataLoader



def create_embeddings_db(model_weights_path, device, image_dir="./data/oxbuild/images/", fts_dir="./fts/"):
    
    # Create transformss
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]
    transforms_test = transforms.Compose([transforms.Resize(560),
                                        transforms.FiveCrop(548),                                 
                                        transforms.Lambda(lambda crops: torch.stack([transforms.ToTensor()(crop) for crop in crops])),
                                        ])

    # Create dataset
    eval_dataset = EvalDataset(image_dir, transforms=transforms_test)
    eval_loader = DataLoader(eval_dataset, batch_size=1, num_workers=0, shuffle=False)

    # Create embedding network
    resnet_model = models.resnet101(pretrained=False)
    model = TripletNet(resnet_model)
    model.load_state_dict(torch.load(model_weights_path))
    model.to(device)
    model.eval()

    # Create features
    with torch.no_grad():
        for image, name in tqdm(eval_loader):
            # Move image to device and get crops
            image = image.to(device)
            bs, ncrops, c, h, w = image.size()

            # Get output
            output = model.get_embedding(image.view(-1, c, h, w))
            output = output.view(bs, ncrops, -1).mean(1).cpu().numpy()

            # Save fts
            save_path = os.path.join(fts_dir, name[0].replace(".jpg", ""))
            np.save(save_path, output)
        


# create_embeddings_db()