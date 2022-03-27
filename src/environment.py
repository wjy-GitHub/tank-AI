#!/usr/bin/python
# coding=utf-8

import tanks
import pygame
import random
import time

EPS = 16 # 一个格子的大小
WIDTH, HEIGHT = 480 // EPS - 4, 416 // EPS


class Environment(tanks.Game):
    """
    在坦克大战游戏的基础上搭建的环境，Agent在此环境中学习玩坦克大战的策略。

    一些有用的信息：
    地图大小为: 水平长 480px，垂直高416px
    坦克的大小为： 32 * 32
    铁块的大小为： 16 * 16
    地图中只用铁和空地两种地形，铁永远无法被破坏。
    玩家和基地始终处于无敌状态。
    """

    def __init__(self, show, debug=False, enemy_num=20):
        """
        环境初始化需要的一些参数和设置，你不需要修改这个函数中的内容

        :param show: 0/1, 是否展示画面
        :param debug: 0/1, 是否打印环境中的信息
        :param enemy_num: int, 一共会刷新多少个敌方坦克
        """

        super().__init__(show=show)

        tanks.castle = tanks.Castle()

        self.game_over = False
        self.stage = 1
        self.nr_of_players = 1
        self.Debug = debug
        self.show = show
        self.enemy_num = enemy_num

        # clear all timers
        del tanks.gtimer.timers[:]
        del tanks.players[:]
        del tanks.bullets[:]
        del tanks.enemies[:]
        del tanks.bonuses[:]
        del tanks.gtimer.timers[:]

        tanks.castle.rebuild()
        self.level = tanks.Level(1)
        self.level.enemies_left = [0] * self.enemy_num
        self.reloadPlayers()
        self.map_track = [0] * WIDTH * HEIGHT
        tanks.gtimer.add(500, lambda: self.spawnEnemy())

        # make castle invulnerable
        self.level.buildFortress(self.level.TILE_STEEL)
        self._init()
        self.action_logs = [-1] * 20  # 原为 * 10


    def _step(self, action):
        """
        运行Agent采取的行动，并反馈采取行动后环境的状态，该动作对应的奖励以及游戏是否结束
        你可以在这个部分添加代码用于获取更多的信息，帮助你完成 _get_state() 和 _get_reward() 这两个函数

        :param action: int， 来自Agent
        0: fire, 1: up, 2: right, 3: down, 4: left, 5: null
        :return:
        state：list of nums, Agent的行动执行后，环境的状态
        reward：a number, 给予Agent的奖励
        done: 1/0/True/False, 游戏是否结束
        """
        self.kill = 0
        time_passed = self.clock.tick(50*tanks.quick)
        # make player invulnerable
        self.shieldPlayer(tanks.players[0], True, None)

        player = tanks.players[0]
        direction = (self.DIR_UP, self.DIR_RIGHT, self.DIR_DOWN, self.DIR_LEFT)

        # 是否显示画面
        # if self.show:
        #     for _ in pygame.event.get():
        #         pass
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit(0)

        del tanks.bonuses[:]

        # 执行动作
        if action == 0:
            player.fire()
        elif action == 5:
            pass
        else:
            player.move(direction[action - 1])
        player.update(time_passed)

        # 更新敌人状态
        for enemy in tanks.enemies:
            if enemy.state == enemy.STATE_DEAD:
                tanks.enemies.remove(enemy)
                self.kill += 1
                if len(self.level.enemies_left) == 0 and len(tanks.enemies) == 0:
                    state, reward = self._get_state(), self._get_reward()
                    self.__checker(state, reward)
                    return state, reward, True
            else:
                enemy.update(time_passed)

        # 更新子弹状态
        for bullet in tanks.bullets:
            if bullet.state == bullet.STATE_REMOVED:
                tanks.bullets.remove(bullet)
            else:
                bullet.update()

        for label in tanks.labels:
            if not label.active:
                tanks.labels.remove(label)

        tanks.gtimer.update(time_passed)

        if self.show:
            self.draw()

        # 更新地图中坦克到达过的位置，记录在此前后未到达位置数量
        curpos = (round((self.get_tanks_position()[0][0] - 3) / EPS), round((self.get_tanks_position()[0][1] - 3) / EPS))
        self.pre_null = list.count(self.map_track, 0)
        self.map_track[curpos[0] + curpos[1] * WIDTH] = 2
        self.map_track[curpos[0] + 1 + curpos[1] * WIDTH] = 2
        self.map_track[curpos[0] + (curpos[1] + 1) * WIDTH] = 2
        self.map_track[curpos[0] + 1 + (curpos[1] + 1) * WIDTH] = 2
        self.after_null = list.count(self.map_track, 0)

        state, reward = self._get_state(), self._get_reward()#TODO something
        self.__checker(state, reward)
        return state, reward, False

    def _reset(self):
        """
        重置环境，并返回初始状态。你不需要修改这个部分。
        :return:
        state，0，False
        """
        self.__init__(show=self.show, debug=self.Debug, enemy_num=self.enemy_num)
        state, reward = self._get_state(), 0
        self.__checker(state, reward)
        return state, reward, False

    def __checker(self, state, reward):
        """
        检查输出的 state 和 reward 是否合法
        不要修改这个函数
        """
        if not isinstance(state, list):
            print(f'_get_state 函数的输出必须是list的形式，你的输出是 {type(state)}!')
            exit(0)
        if not isinstance(reward, int) and not isinstance(reward, float):
            print(f'_get_reward 函数的输出必须是一个数字(int/float)，你的输出是 {type(reward)}!')
            exit(0)
        for item in state:
            if not isinstance(item, int) and not isinstance(item, float):
                print(f'_get_state 函数的输出的state的内容必须都是数字，你的输出包含 {type(item)}!')
                exit(0)


    def get_action_logs(self):
        """
        返回动作的历史记录（前20步，包括本次动作，即本次动作的编号是列表的最后一个元素）

        :return: A list
        """
        return self.action_logs

    def get_tanks_position(self):
        """
        返回所有坦克的位置， 包括自己
        各坦克的位置，由其占用的32*32区域的左上角的像素点的位置表示
        即坦克仅转动方向不影响其位置

        :return:
        player_pos: a Tuple
        en_pos: a list of Tuple
        """
        player_pos = tanks.players[0].rect.topleft
        en_pos = [en.rect.topleft for en in tanks.enemies]
        return player_pos, en_pos

    def get_tanks_direction(self):
        """
        返回所有坦克的朝向， 包括自己

        :return:
        player_dir: int
        en_dir: a list of int
        """
        player_dir = tanks.players[0].direction
        en_dir = [en.direction for en in tanks.enemies]
        return player_dir, en_dir

    def get_killed_nums(self):
        """
        统计敌人数量信息
        :return:
        1）当前时间点击杀敌人数量
        2）历史击杀敌人数量
        3）场上存货敌人数量
        4）剩余未刷新敌人数量
        """

        left = len(self.level.enemies_left)
        alive = len(tanks.enemies)
        killed = self.enemy_num - alive - left
        return self.kill, killed, alive, left

    def get_steel_position(self):
        """
        返回所有铁块的位置
        各铁块的位置，由其占用的16*16区域的左上角的像素点的位置表示

        :return:
        steel_pos: a list of Tuple
        """
        steel_pos = [tile.topleft for tile in self.level.mapr if tile.type == self.level.TILE_STEEL]
        return steel_pos


    def _init(self):
        """
        你需要修改这个部分
        这一函数与_get_reward()函数的设计与修改一共应占你工作时间的30%以上

        设计奖励函数，指导Agent学习。
        你可以根据自己的想法修改这个函数中的变量，以及添加/删除其他的变量。
        """

        self.laststate = [(self.get_tanks_position()[0][0] - 3,self.get_tanks_position()[0][1] - 3),]#修改为 a list of tuple
        # 对地图上的障碍物铁块进行记录
        for tup in self.get_steel_position():
            self.map_track[tup[0]//EPS + (tup[1]//EPS) * WIDTH] = 1
        # 记录初始坦克所在位置，为到达过的位置，初始化未到达位置数量
        self.map_track[round((self.get_tanks_position()[0][0] - 3) / EPS) + round((self.get_tanks_position()[0][1] - 3) / EPS)  * WIDTH] = 2
        self.map_track[round((self.get_tanks_position()[0][0] - 3) / EPS) + (round((self.get_tanks_position()[0][1] - 3) / EPS) + 1) * WIDTH] = 2
        self.map_track[round((self.get_tanks_position()[0][0] - 3) / EPS) + 1 + round((self.get_tanks_position()[0][1] - 3) / EPS) * WIDTH] = 2
        self.map_track[round((self.get_tanks_position()[0][0] - 3) / EPS) + 1 + (round((self.get_tanks_position()[0][1] - 3) / EPS) + 1) * WIDTH] = 2
        self.pre_null, self.after_null = list.count(self.map_track, 0), list.count(self.map_track, 0)

    def _get_reward(self):
        """
        你需要修改这个部分
        这一函数与_init()函数的设计与修改一共应占你工作时间的30%以上

        该函数返回的 必须 是一个数字！
        :return: a number, int/float
        """

        # 本奖励函数思想：走得离前20步越远越好。越近奖励越低
        # 如果采用这个奖励函数，您最后看到的训练效果，会是坦克上下移动或者在顶部左右移动，来使得自己的奖励最大化
        # 在训练过程中，您会看到奖励会不断增加，证明坦克训练正常
        # 修正坦克像素坐标，-3,A tuple containing two numbers
        curpos = ((self.get_tanks_position()[0][0] - 3),(self.get_tanks_position()[0][1] - 3))
        reward = 0
        # 当坦克到达全新位置，对其进行奖励，随着未到达地区减少奖励增加
        if self.pre_null != self.after_null:
            reward = reward + abs(self.pre_null - self.after_null) * list.count(self.map_track,2) * 10
        flag = False
        # 判断当前位置是否和前二十步位置重合
        for s in self.laststate:
            if s[0] == curpos[0] and s[1] == curpos[1]:
                flag = True
                break
        if not flag:
            for s in self.laststate:
                reward = reward + abs(s[0] - curpos[0]) + abs(s[1] - curpos[1])
            # 只有不重复的位置才被记录，防止坦克原地不动
            self.laststate.append(curpos)
        else:
            for s in self.laststate:
                reward = reward - (abs(s[0] - curpos[0]) + abs(s[1] - curpos[1])) / 2

        # reward = reward + abs(l[0] - curpos[0]) - 5
        # reward = reward + abs(l[1] - curpos[1]) - 5
        while len(self.laststate) > 20:
            self.laststate.pop(0)

        return reward

    def _get_state(self):
        """
        你需要填补这一部分的内容，你的主要时间（50%+） 应该用于修改这个函数

        返回当前时间点下的环境状态给Agent，其中需要尽可能包含对Agent学习
        有用的信息，摒弃无用的信息。

        该函数返回的 必须 是一个list， list的元素 必须 都是数字
        :return: List of numbers
        1）2）坦克当前坐标，
        3）4）上一步坐标，
        5）6）7）8）当前坦克的四个方向是否存在障碍物 True / False
        """

        # 坦克的地图格子坐标
        tank_pos_x = round((self.get_tanks_position()[0][0] - 3) / EPS)
        tank_pos_y = round((self.get_tanks_position()[0][1] - 3) / EPS)
        #坦克周围四个方向，每个方向各两个格子
        if (tank_pos_x - 1) < 0:
            en_left_up, en_left_down = 1, 1
        else:
            en_left_up = self.map_track[(tank_pos_x - 1) + tank_pos_y * WIDTH]
            en_left_down = self.map_track[(tank_pos_x - 1) + (tank_pos_y + 1) * WIDTH]
        if (tank_pos_y - 1) < 0:
            en_up_left, en_up_right = 1, 1
        else:
            en_up_left = self.map_track[tank_pos_x + (tank_pos_y - 1) * WIDTH]
            en_up_right = self.map_track[(tank_pos_x + 1) + (tank_pos_y - 1) * WIDTH]
        if (tank_pos_x + 2 >= WIDTH):
            en_right_up, en_right_down = 1, 1
        else:
            en_right_up = self.map_track[(tank_pos_x + 2) + tank_pos_y * WIDTH]
            en_right_down = self.map_track[(tank_pos_x + 2) + (tank_pos_y + 1) * WIDTH]
        if (tank_pos_y + 2 >= HEIGHT):
            en_down_left, en_down_right = 1, 1
        else:
            en_down_left = self.map_track[tank_pos_x + (tank_pos_y + 2) * WIDTH]
            en_down_right = self.map_track[(tank_pos_x + 1) + (tank_pos_y + 2) * WIDTH]

        # 判断坦克四个方向的通行条件
        up_access = False if en_up_left == 1 or en_up_right == 1 else True
        right_access = False if en_right_up == 1 or en_right_down == 1 else True
        down_access = False if en_down_left == 1 or en_down_right == 1 else True
        left_access = False if en_left_up == 1 or en_left_down == 1 else True
        # 状态直接返回玩家坦克的坐标 =》返回坦克当前坐标，上一步坐标，当前坦克的四个方向是否存在障碍物
        # [tank_pos_x,tank_pos_y,tank_dir,en_up_left,en_up_right,en_right_up,en_right_down,en_down_right,en_down_left,en_left_down,en_left_up] + self.map_track
        # print(tank_pos_x,tank_pos_y,tank_dir,up_access,right_access,down_access,left_access)
        return [tank_pos_x,tank_pos_y,round(self.laststate[-1][0] / EPS),round(self.laststate[-1][1] / EPS),up_access,right_access,down_access,left_access]


if __name__ == '__main__':
    en = Environment(show=1, debug=0, enemy_num=2)
    print(en.get_tanks_direction())
    print(en.get_tanks_position()[0][0],",",en.get_tanks_position()[0][1])
    # for pos in en.get_steel_position():
    #     if pos[0] == 32:
    #         print(pos)
    print(en.map_track[54],en.map_track[55],en.map_track[58],en.map_track[59],en.map_track[61])
    print(en.map_track[338], en.map_track[339], en.map_track[341])
    print(en.get_action_logs())
    print(en.get_tanks_position())
    print(en.laststate[0])
    print(1 & 0, 0 & 0, 1 & 1)
    print(list.count(en.map_track,2))
    print(2 & 2)