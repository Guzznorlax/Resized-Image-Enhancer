import torch
import torchvision
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import random
from tensorboardX import SummaryWriter 

# upsample from 32x32 to 128x128


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()

        self.batch_size = 64
        self.num_epoch = 20

        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

        self.conv1 = nn.Conv2d(in_channels=3, out_channels=256, kernel_size=3, stride=2, padding=0)
        self.relu1 = nn.ReLU()

        self.conv2 = nn.Conv2d(in_channels=256, out_channels=512, kernel_size=3, stride=2, padding=0)
        self.relu2 = nn.ReLU()

        self.conv3 = nn.Conv2d(in_channels=512, out_channels=1024, kernel_size=3, stride=2, padding=0)
        self.relu3 = nn.ReLU()

        self.decv1 = nn.ConvTranspose2d(in_channels=1024, out_channels=1024, kernel_size=3, stride=2, padding=0)
        self.relu4 = nn.ReLU()

        self.decv2 = nn.ConvTranspose2d(in_channels=1024, out_channels=512, kernel_size=3, stride=2, padding=0)
        self.relu5 = nn.ReLU()

        self.decv3 = nn.ConvTranspose2d(in_channels=512, out_channels=3, kernel_size=4, stride=2, padding=0)
        self.relu6 = nn.ReLU()

        self.tanh = nn.Tanh()

    def forward(self, x):
        x = self.conv1(x)
        x = self.relu1(x)

        x = self.conv2(x)
        x = self.relu2(x)

        x = self.conv3(x)
        x = self.relu3(x)

        x = self.decv1(x)
        x = self.relu4(x)

        x = self.decv2(x)
        x = self.relu5(x)

        x = self.decv3(x)
        x = self.relu6(x)

        x = self.tanh(x)

        return x


def train(model, optimizer, data_path, batch_size, num_epochs, curr_epoch, curr_iter, writer, model_path, state_path):
    print("[INFO] Start training session")

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print("[INFO] Device:", device)

    print("[INFO] Loading dataset...")
    train_dataset = load_dataset(data_path)

    train_loader = torch.utils.data.DataLoader(
        train_dataset,
        batch_size=batch_size,
        num_workers=0,
        shuffle=True
    )
    print("[INFO] Finished loading dataset")

    criterion = nn.L1Loss()

    print("[INFO] Start training")
    for epoch in range(curr_epoch + 1, curr_epoch + num_epochs + 1):
        print('[ITER] Starting epoch:', "[" + str(curr_epoch + 1) + "/" + str(curr_epoch + num_epochs) + "]")
        for batch_idx, (data, label) in enumerate(train_loader):
            data = data.to(device=device)

            scale = random.uniform(1, 4)
            resized_data = F.interpolate(data, int(data.size(2) / scale))
            resized_data = F.interpolate(resized_data, data.size(2))

            output = model(resized_data)

            diff = data - output
            diff = diff.mean().unsqueeze(-1)
            # print("[DEBUG] diff size:", diff.size())

            target = torch.FloatTensor([0])
            target = target.to(device=device)
            # print("[DEBUG] target size:", target.size())

            loss = criterion(diff, target)

            writer.add_scalar("loss", loss.item(), curr_iter)

            print('[ITER] Iteration:', curr_iter)
            print('[LOSS] Loss:', loss.item())

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            curr_iter += 1

            if curr_iter % 50 == 0:
                save_model(model, model_path, curr_epoch)
                save_state(model, epoch, curr_iter, optimizer, state_path)


def train_from_checkpoint(model, state_path, data_path, batch_size, num_epochs, writer):
    optimizer = optim.Adam(model.parameters(), lr=2e-4)
    curr_epoch, curr_iter = load_state(model, optimizer, state_path)
    train(model, optimizer, data_path, batch_size, num_epochs, curr_epoch, curr_iter, writer)


def train_from_start(model, data_path, batch_size, num_epochs, writer):
    optimizer = optim.Adam(model.parameters(), lr=2e-4)
    train(model, optimizer, data_path, batch_size, num_epochs, 0, 0, writer)


def save_state(model, curr_epoch, curr_iter, optimizer, path):
    path = path + "upsampling_test" + '_{}.tar'.format(curr_epoch)
    torch.save({
        'curr_epoch': curr_epoch,
        'curr_iter': curr_iter,
        'model_state_dict': model.state_dict(),
        'optim_state_dict': optimizer.state_dict(),
    }, path)


def load_state(model, optimizer, load_path):
    checkpoint = torch.load(load_path)
    model.load_state_dict(checkpoint["model_state_dict"])
    optimizer.load_state_dict(checkpoint["optim_state_dict"])
    curr_epoch = checkpoint["curr_epoch"]
    curr_iter = checkpoint["curr_iter"]

    return curr_epoch, curr_iter


def save_model(model, name, save_path, curr_epoch):
    file_path = (save_path + name + '_{}.pt'.format(curr_epoch))
    torch.save(model.state_dict(), file_path)
    print("[INFO] Model saved")


def load_dataset(data_path):
    train_dataset = torchvision.datasets.ImageFolder(
        root=data_path,
        transform=torchvision.transforms.ToTensor()
    )
    return train_dataset
