import torch
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
from torchvision import transforms, models
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm

NUM_EPOCHS = 50
# transformation
normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])

compose = transforms.Compose([transforms.Resize((224, 224)),
                               transforms.ToTensor(),
                               normalize])

# init datasets
traindata = ImageFolder("COVIDNet_ImageFolder/train", transform=compose)
testdata = ImageFolder("COVIDNet_ImageFolder/test", transform=compose)

train_len = int(0.9*len(traindata))
traindata, validdata = torch.utils.data.random_split(traindata, [train_len, len(traindata)-train_len], generator=torch.Generator().manual_seed(42))

# init dataloader
train_loader = DataLoader(traindata, batch_size=64, shuffle=True)
test_loader = DataLoader(testdata)

# init model and copy weights
network = models.resnet50(pretrained=False)
network.load_state_dict(torch.load("models/converted_vissl_swav_covid_e950.torch"), strict=False)
network.fc = nn.Linear(2048, 3)
network.fc.weight.data.normal_(mean=0.0, std=0.01)
network.fc.bias.data.zero_()

# for name, parameter in network.named_parameters():
#     if any(layer in name for layer in ['fc']):
#         parameter.requires_grad = True
#         print(name)
#     else:
#         parameter.requires_grad = False

network = network.cuda()
network.train()
print(network)

criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(network.parameters(), lr=0.0002)

for epoch in range(NUM_EPOCHS):
    sum_loss = 0
    total = 0
    correct = 0
    for data, label in tqdm(train_loader):
        data = data.cuda()
        label = label.cuda()
        out = network(data)
        loss = criterion(out, label)
        sum_loss += loss.item()
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        _, predicted = torch.max(out.data, 1)
        total += label.size(0)
        correct += (predicted == label).sum().item()

    print(f'Accuracy:{correct/total}')
    print(f"epoch: {epoch}, Train Loss: {sum_loss/len(train_loader)}")
    torch.save(network.state_dict(), f"models/converted_vissl_swav_covid_e950_e{epoch}_fc_only.torch")
