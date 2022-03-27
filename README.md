# tank-AI
###坦克大战AI训练  
重写了_init(), _get_reward(),_get_state(),对_step()进行了添加部分代码。  
实现了坦克在地图中的自由移动功能（基础必做部分） 
####使用方法：  
**运行train.py，修改对应参数**
* 训练智能体:
```config = {
        'task': 'explore',
        'test': False,
        'save': 5,
        'show': 5,
        'continue_last_train': True,
    }
```
* 运行训练好的智能体:
```
config = {
        'task': 'explore',
        'test': 'log_1365.pkl',
        'save': 5,
        'show': 5,
        'continue_last_train': True,
    }
```
* 参数说明：
    task:当前训练任务，explore:探索地图。  
    test:False,训练智能体；str,加载str对应路径存储的智能体，展示训练结果。  
    >例如：log_1365.pkl，代表的是第1365轮训练得到的智能体(/scc/logs/explore/log_1365.pkl)  
     
    save:5，每5轮保存一次智能体  
    show:5，每5轮展示一下训练结果
####设计思路： 
* init:  
记录坦克前二十步的像素坐标位置(self.laststate)，为了防止坦克原地不动，只记录不同位置的坐标。  
利用一个地图WIDTH * HEIGHT大小的一维数组(self.map_track)（初始为0），记录地图中铁块（障碍物）所在的位置（置1）和坦克到达过的位置（置2）。
* reward:    
主线奖励：  
坦克当前位置(curpos)与前二十步所有位置不同，对其进行加分；  
坦克但前位置(curpos)与前二十步位置重合，则对其进行减分；  
加减分具体算法：计算本次坐标与前二十步坐标绝对差之和。  
支线奖励：  
坦克到达全新位置时，根据当前所剩未到达位置数量，进行奖励，未到达位置数量越少，奖励越多。  
原因：未到达位置随着游戏进行，越来越稀少，奖励需要增加。
* state:  
返回坦克当前坐标(curpos)，前一步坐标(self.laststate[-1]),四个方向的通行条件(True/False).  
根据当前坐标位置(curpos)和记录的地图数据(self.map_track)，判断坦克四个方向的通行条件。