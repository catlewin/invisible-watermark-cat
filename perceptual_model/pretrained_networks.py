from collections import namedtuple
import torch
from torchvision import models as tv
from torchvision.models import (
    AlexNet_Weights,
    VGG16_Weights,
    SqueezeNet1_1_Weights,
    ResNet18_Weights,
    ResNet34_Weights,
    ResNet50_Weights,
    ResNet101_Weights,
    ResNet152_Weights,
)

class squeezenet(torch.nn.Module):
    def __init__(self, requires_grad=False, pretrained=True):
        super(squeezenet, self).__init__()
        weights = SqueezeNet1_1_Weights.IMAGENET1K_V1 if pretrained else None
        pretrained_features = tv.squeezenet1_1(weights=weights).features
        self.slice1 = torch.nn.Sequential()
        self.slice2 = torch.nn.Sequential()
        self.slice3 = torch.nn.Sequential()
        self.slice4 = torch.nn.Sequential()
        self.slice5 = torch.nn.Sequential()
        self.slice6 = torch.nn.Sequential()
        self.slice7 = torch.nn.Sequential()
        self.N_slices = 7
        for x in range(2):
            self.slice1.add_module(str(x), pretrained_features[x])
        for x in range(2,5):
            self.slice2.add_module(str(x), pretrained_features[x])
        for x in range(5, 8):
            self.slice3.add_module(str(x), pretrained_features[x])
        for x in range(8, 10):
            self.slice4.add_module(str(x), pretrained_features[x])
        for x in range(10, 11):
            self.slice5.add_module(str(x), pretrained_features[x])
        for x in range(11, 12):
            self.slice6.add_module(str(x), pretrained_features[x])
        for x in range(12, 13):
            self.slice7.add_module(str(x), pretrained_features[x])
        if not requires_grad:
            for param in self.parameters():
                param.requires_grad = False

    def forward(self, X):
        h = self.slice1(X); h_relu1 = h
        h = self.slice2(h); h_relu2 = h
        h = self.slice3(h); h_relu3 = h
        h = self.slice4(h); h_relu4 = h
        h = self.slice5(h); h_relu5 = h
        h = self.slice6(h); h_relu6 = h
        h = self.slice7(h); h_relu7 = h
        vgg_outputs = namedtuple("SqueezeOutputs", ['relu1','relu2','relu3','relu4','relu5','relu6','relu7'])
        return vgg_outputs(h_relu1,h_relu2,h_relu3,h_relu4,h_relu5,h_relu6,h_relu7)

class alexnet(torch.nn.Module):
    def __init__(self, requires_grad=False, pretrained=True):
        super(alexnet, self).__init__()
        weights = AlexNet_Weights.IMAGENET1K_V1 if pretrained else None
        alexnet_pretrained_features = tv.alexnet(weights=weights).features
        self.slice1 = torch.nn.Sequential()
        self.slice2 = torch.nn.Sequential()
        self.slice3 = torch.nn.Sequential()
        self.slice4 = torch.nn.Sequential()
        self.slice5 = torch.nn.Sequential()
        self.N_slices = 5
        for x in range(2):
            self.slice1.add_module(str(x), alexnet_pretrained_features[x])
        for x in range(2, 5):
            self.slice2.add_module(str(x), alexnet_pretrained_features[x])
        for x in range(5, 8):
            self.slice3.add_module(str(x), alexnet_pretrained_features[x])
        for x in range(8, 10):
            self.slice4.add_module(str(x), alexnet_pretrained_features[x])
        for x in range(10, 12):
            self.slice5.add_module(str(x), alexnet_pretrained_features[x])
        if not requires_grad:
            for param in self.parameters():
                param.requires_grad = False

    def forward(self, X):
        h = self.slice1(X); h_relu1 = h
        h = self.slice2(h); h_relu2 = h
        h = self.slice3(h); h_relu3 = h
        h = self.slice4(h); h_relu4 = h
        h = self.slice5(h); h_relu5 = h
        alexnet_outputs = namedtuple("AlexnetOutputs", ['relu1', 'relu2', 'relu3', 'relu4', 'relu5'])
        return alexnet_outputs(h_relu1, h_relu2, h_relu3, h_relu4, h_relu5)

class vgg16(torch.nn.Module):
    def __init__(self, requires_grad=False, pretrained=True):
        super(vgg16, self).__init__()
        weights = VGG16_Weights.IMAGENET1K_V1 if pretrained else None
        vgg_pretrained_features = tv.vgg16(weights=weights).features
        self.slice1 = torch.nn.Sequential()
        self.slice2 = torch.nn.Sequential()
        self.slice3 = torch.nn.Sequential()
        self.slice4 = torch.nn.Sequential()
        self.slice5 = torch.nn.Sequential()
        self.N_slices = 5
        for x in range(4):
            self.slice1.add_module(str(x), vgg_pretrained_features[x])
        for x in range(4, 9):
            self.slice2.add_module(str(x), vgg_pretrained_features[x])
        for x in range(9, 16):
            self.slice3.add_module(str(x), vgg_pretrained_features[x])
        for x in range(16, 23):
            self.slice4.add_module(str(x), vgg_pretrained_features[x])
        for x in range(23, 30):
            self.slice5.add_module(str(x), vgg_pretrained_features[x])
        if not requires_grad:
            for param in self.parameters():
                param.requires_grad = False

    def forward(self, X):
        h = self.slice1(X); h_relu1_2 = h
        h = self.slice2(h); h_relu2_2 = h
        h = self.slice3(h); h_relu3_3 = h
        h = self.slice4(h); h_relu4_3 = h
        h = self.slice5(h); h_relu5_3 = h
        vgg_outputs = namedtuple("VggOutputs", ['relu1_2', 'relu2_2', 'relu3_3', 'relu4_3', 'relu5_3'])
        return vgg_outputs(h_relu1_2, h_relu2_2, h_relu3_3, h_relu4_3, h_relu5_3)

class resnet(torch.nn.Module):
    def __init__(self, requires_grad=False, pretrained=True, num=18):
        super(resnet, self).__init__()
        if num == 18:
            weights = ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
            self.net = tv.resnet18(weights=weights)
        elif num == 34:
            weights = ResNet34_Weights.IMAGENET1K_V1 if pretrained else None
            self.net = tv.resnet34(weights=weights)
        elif num == 50:
            weights = ResNet50_Weights.IMAGENET1K_V1 if pretrained else None
            self.net = tv.resnet50(weights=weights)
        elif num == 101:
            weights = ResNet101_Weights.IMAGENET1K_V1 if pretrained else None
            self.net = tv.resnet101(weights=weights)
        elif num == 152:
            weights = ResNet152_Weights.IMAGENET1K_V1 if pretrained else None
            self.net = tv.resnet152(weights=weights)

        self.N_slices = 5

        self.conv1 = self.net.conv1
        self.bn1 = self.net.bn1
        self.relu_layer = self.net.relu  # 🔁 renamed from self.relu to avoid conflict
        self.maxpool = self.net.maxpool
        self.layer1 = self.net.layer1
        self.layer2 = self.net.layer2
        self.layer3 = self.net.layer3
        self.layer4 = self.net.layer4

        if not requires_grad:
            for param in self.parameters():
                param.requires_grad = False

    def forward(self, X):
        h = self.conv1(X)
        h = self.bn1(h)
        h = self.relu_layer(h)  # ✅ uses renamed relu
        h_relu1 = h
        h = self.maxpool(h)
        h = self.layer1(h)
        h_conv2 = h
        h = self.layer2(h)
        h_conv3 = h
        h = self.layer3(h)
        h_conv4 = h
        h = self.layer4(h)
        h_conv5 = h

        outputs = namedtuple("Outputs", ['relu1', 'conv2', 'conv3', 'conv4', 'conv5'])
        return outputs(h_relu1, h_conv2, h_conv3, h_conv4, h_conv5)
