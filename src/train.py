import time
import torch
import pickle
import os
from collections import defaultdict

import tanks
from agent import AgentVPG
import environment as Env


def reward_to_go(rews, gamma=0.9):
    """
    计算神经网络更新时需要的一些参数
    不要修改这个函数
    """
    n = len(rews)
    rtgs = torch.zeros_like(torch.tensor(rews))
    for i in reversed(range(n)):
        rtgs[i] = rews[i] + (rtgs[i+1] * gamma if i+1 < n else 0)
    return rtgs


def run_one_episode(env, agent, batch, max_step=200):
    """
    在环境中模拟一局游戏，收集数据
    非必要情况下不需要修改这个函数

    :param env: 虚拟环境
    :param agent: 强化学习智能体
    :param batch: 用于收集数据的字典
    :param max_step: 与环境交互的最大次数
    :return:
    ep_ret: float， 本局游戏的总奖励数
    ep_len: int， 本局游戏的时长
    killed_enemy: int， 本局游戏中被击杀的敌人数量
    done: bool， 本局游戏是否结束（敌人是否被全部击杀）
    """
    obs, _, _ = env._reset()  # first obs comes from starting distribution
    ep_rews = []  # list for rewards accrued throughout ep

    while True:
        # save obs
        batch['obs'].append(obs.copy())

        # act in the environment
        act = agent.choose_action(torch.as_tensor(obs, dtype=torch.float32))
        rew = 0
        for _ in range(8):
            obs, rew1, done = env._step(act)
            rew = rew + rew1
            if done:
                break
        
        rew = rew / 8
        
        env.action_logs.pop(0)
        env.action_logs.append(act)


        batch['acts'].append(act)
        ep_rews.append(rew)

        # 当game over或者交互次数超出上限时
        if done or len(ep_rews) >= max_step:
            # if episode is over, record info about episode
            ep_ret, ep_len = sum(ep_rews), len(ep_rews)
            batch['rets'].append(ep_ret)
            batch['lens'].append(ep_len)
            batch['weights'] = list(reward_to_go(ep_rews))
            killed_enemy = env.enemy_num - len(env.level.enemies_left) - len(tanks.enemies)
            return ep_ret, ep_len, killed_enemy, done


def train(task='explore', test=False, save=10, show=10, **kwargs):
    """
    主程序
    当中的参数可以略作修改，但时间不应超过10%

    建议尝试的参数：
    max_step, batch_size

    :param task: str, explore/play
        explore: 训练agent让其学会探索地图
        play: 让agent玩坦克大战第一关

    :param test: False/str，
        False表示此时为训练智能体，非False时为训练好的智能体所在的路径
    :param save: save agent every 'save' episodes
    :param show: show agent behavior every 'show' episodes
    :return: None
    """
    if task not in ['explore', 'play']:
        return
    elif task == 'explore':
        flag = True
    else:
        flag = False

    action_space = range(6)
    max_episode = 10000
    tanks.quick = 0

    if flag:
        batch_size = 512
        max_step = 512
        enemy_num = 0
    else:
        batch_size = 1024
        max_step = 1024 * 2
        enemy_num = 5

    batch = {'obs': [], 'acts': [], 'weights': [], 'rets': [], 'lens': []}

    if test:
        tanks.quick = 5
        env = Env.Environment(show=1, debug=0, enemy_num=enemy_num)
        obs, _, _ = env._reset()
        with open(f'logs/{task}/{test}', 'rb') as f:
            agent = torch.load(f)
    else:
        last_train_path = f'logs/{task}/last_train.pkl'
        env = Env.Environment(show=0, debug=0, enemy_num=enemy_num)
        obs, _, _ = env._reset()
        obs_dim = len(obs)
        if kwargs.get('continue_last_train', False) and os.path.isfile(last_train_path):
            with open(last_train_path, 'rb') as f:
                agent, start_epi = pickle.load(f)
            print(f'接着上次的训练结果继续训练，之前已训轮数：{start_epi}')
        else:
            if kwargs.get('continue_last_train', False):
                print('找不到上次训练后存储的记录，现在将重新开始训练...')
            start_epi = 0
            agent = AgentVPG(action_space=action_space, obs_dim=obs_dim)

    t = time.time()
    loss = []
    kill_log = []
    time_cost_log = []
    for epi in range(start_epi + 1, max_episode):

        mean_rewards = []
        ep_ret, ep_len, killed_enemy, done = run_one_episode(env, agent, batch, max_step)

        for i in range(len(batch['obs'])//batch_size):
            tmp = {}
            for key in batch:
                tmp[key] = batch[key][i*batch_size:i*batch_size+batch_size]
            loss.append(agent.update(tmp))

        batch = {'obs': [], 'acts': [], 'weights': [], 'rets': [], 'lens': []}
        mean_rewards.append(ep_ret)
        kill_log.append(killed_enemy)
        time_cost_log.append(ep_len)
        if epi % 1 == 0 and not test:
            print(f'Episode {epi}:\ntime: {time.time() - t}\t'
                  f'current reward: {sum(mean_rewards)/len(mean_rewards)}')
            loss = []
            if not flag:
                print(f'kill log :{kill_log}')
                print(f'time cost log ： {time_cost_log}')
            kill_log = []
            time_cost_log = []
            with open(f'logs/{task}/last_train.pkl', 'wb') as f:
                pickle.dump([agent, epi], f)

        if epi % save == 0 and not test:
            with open(f'logs/{task}/log_{epi}.pkl', 'wb') as f:
                torch.save(agent, f)
        if epi % show == 0 and not test:
            env.show = 1
            tanks.quick = 5
            run_one_episode(env, agent, defaultdict(list), max_step)
            tanks.quick = 0
            env.show = 0


if __name__ == '__main__':
    config = {
        'task': 'explore',
        'test': False,
        'save': 5,
        'show': 5,
        'continue_last_train': True,
    }  # 参数的说明在 train 函数中

    train(**config)
