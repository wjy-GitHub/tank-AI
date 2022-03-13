import random
import torch
from torch.optim import Adam
from torch.distributions.categorical import Categorical

from net import MLP


cuda_condition = torch.cuda.is_available()
device = torch.device('cuda:0' if cuda_condition else 'cpu')


class AgentVPG:
    """
    Agent

    functions:
    1) choose_action
        input - state of the current environment
        output - an action
    2) update
        input - experience obtained by interacting with the environment
        output - losses
    """

    def __init__(self, action_space, obs_dim, gamma=1):
        self.logits_net = MLP(input_dim=obs_dim, output_dim=len(action_space))
        self.act_space = list(action_space)
        self.optim = Adam(self.logits_net.parameters(), lr=5e-3)

    # make action selection function (outputs int actions, sampled from policy)
    def choose_action(self, obs):
        with torch.no_grad():
            return self._get_policy(obs).sample().item()

    def update(self, batch):
        obs = torch.as_tensor(batch['obs'], dtype=torch.float32)
        act = torch.as_tensor(batch['acts'], dtype=torch.int32)
        weights = torch.as_tensor(batch['weights'], dtype=torch.float32)
        batch_loss = self._compute_loss(obs, act, weights)
        self.optim.zero_grad()
        batch_loss.backward()
        self.optim.step()
        return batch_loss.item()

    # make loss function whose gradient, for the right data, is policy gradient
    def _compute_loss(self, obs, act, weights):
        logp = self._get_policy(obs).log_prob(act)
        # print(logp[:10], act[:10])
        return -(logp * weights).mean() + (0.2 * logp).mean()

    # make function to compute action distribution
    def _get_policy(self, obs):
        logits = self.logits_net(obs)
        return Categorical(logits=logits)

