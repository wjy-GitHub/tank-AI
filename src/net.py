import torch
from torch import nn


cuda_condition = torch.cuda.is_available()
device = torch.device('cuda:0' if cuda_condition else 'cpu')


class MLP(nn.Module):
    """
    ...
    """

    def __init__(self, input_dim, output_dim, hidden_dim=32):
        super(MLP, self).__init__()
        # self.cnn = nn.Sequential(
        #     nn.Conv2d(1, 1, (3, 3), 2),
        #     nn.ReLU(),
        # )

        self.mlp = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )

    def forward(self, state):
        # b_s = state.size()[0] if len(state.size()) > 1 else 1
        # state = self.cnn(state.view(b_s, 1, 15, 15))
        out = self.mlp(state)
        return out
