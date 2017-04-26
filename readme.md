# `IJCAI17口碑商家客流量预测 解题思路`

Flamingo Rank4

李中杰，姚易辰

清华大学热能系，清华大学工程力学系

lizhongjie1989@163.com,     yaoyichen@aliyun.com



----------

## 1 赛题概述
- 背景：阿里巴巴和蚂蚁金服逐渐积累了来自用户和商家的海量线上线下交易数据。蚂蚁金服的O2O平台“口碑”使用这些数据为商家提供了包括交易统计，销售分析和销售建议等定制的后端商业智能服务。
- 赛题官网: [阿里天池IJCAI17](https://tianchi.aliyun.com/competition/introduction.htm?spm=5176.100067.5678.1.amifQx&raceId=231591 "阿里天池 IJCAI17") 
- 赛题目标：通过阿里口碑网2000个商户从2015.07.01到2016.10.31的商家数据，用户支付行为数据以及用户浏览行为数据，预测商家在未来14天（2016.11.01-2016.11.14）的客户流量。
- 测评函数：
<div  align="center"> <img src="http://static.zybuluo.com/Jessy923/k6olhzfz2si5p3n57d5w306x/costF.png" width="650" height="150" alt="Item-based filtering" /></div>
- 本次比赛鼓励参赛选手使用外部数据，如天气数据等。

----------


## 2 外部数据及数据清洗
### 2.1外部数据 
外部数据分为机场天气数据和节假日信息两部分，均存储在additional 文件夹下，具体如下：
### 2.1.1 机场天气数据

 - 机场天气数据来源：https://www.wunderground.com
 - 降水量：表格为PRECIP.csv
 - 采样周期为日，爬取程序为Weather_underground_day.py。
 - 详细天气：表格为WEATHER_raw.csv，各地采样间隔不定，最短为30min，最长为3h，爬取程序为 Weather_underground_hour.py。
 - 降水指数和天晴指数：feature/WEATHER_CON_LEVEL.csv 中RAIN_IND及CLEAR_IND对应列。
 - 人体舒适度指数：SSD=(1.818t+18.18)(0.88+0.002f)+(t-32)/(45-t)-3.2v+18.2
其中：温度t，湿度f，风速v
 - 城市天气确定：通过城市经纬度计算城市到各机场距离，城市对应天气采用与之最近的机场信息。

### 2.1.2 节假日信息
节假日信息 HOLI.csv，工作日标签为0，周末标签为1，假期标签为2。表格来源为比赛官方论坛。


### 2.2数据清洗
数据清洗包含两部分，通过规则清除及通过模型预训练清除。
#### 2.2.1规则清除

- 对于单用户某小时内购买行为，采用  处理消除异常消费。
- 开业前7天数据不用于训练集，销量间断前后1天数据不用于训练集。
- 销量以历史过去14天销量的![eq1.png-0.4kB][7]为限制，其中![CodeCogsEqn.png-0.2kB][5]为均值，![sigma.png-0.2kB][6]为均方根。

#### 2.2.2模型预训练清除：
详见第三部分。对于规则难以清除的脏数据，采用预训练的方式清除。模型训练中首先采用欠拟合的算法模型预训练，并清除残差最大的10%(xgboost1,GBDT)和25%(xgboost2)的样本。


----------


## 3 预测模型
![pipeline.JPG-84.2kB][2]
我们团队解题方案的整体架构如上图所示，最终销量预测结果由未来14天常规销量预测及双11修正系数预测两步两部分组成。通过双11修正系数，分别对于2016-11-11，2016-11-12，2016-11-13三天的销量按照1.0，0.2，0.1倍的系数作乘法修正。双11修正部分训练采用xgboost单模型，特征为商家特征信息，标签为2015年双11当天的销量增量百分比。常规销量预测部分，采用基本模型有4套，分别为2套xgboost模型(特征处理及数据清洗程度不同)，GBDT模型和均值模型。对于模型训练的具体说明如下：

### 3.1 常规销量预测模型
#### 3.1.1特征与标签


|    特征与标签	   |   说明    | 
| :-----:   | :-------------:  | 
|历史销量特征|	过去21天的历史销量| 
|节假日特征	|过去21天及预测14天的节假日标注| 
|天气特征	|过去21天及预测当天附近4天(之前两天，当天，之后一天)的降水量，人体舒适度SSD值，SSD值日增量，降水指数，天晴指数|
|商家特征|	平均View/Pay比值，平均每天开店时间，关店时间，开店总时长；首次营业日期，非节假日销量中位数，节假日销量中位数，节假日/非节假日销量比值；商家类别，人均消费，评分，评论数，门店等级| 
|标签	|未来14天日销量|

#### 3.1.2 训练方式
- 采用滑窗对于2000个商家生成481143条有效训练样本，清除间断前后及异常值后保留468535条样本。
+ 采用2次训练的方法，第一次采用最大深度为3欠拟合模型进一步清洗脏数据。采用了xgboost与sklearn的GBDT模型训练，具体参数如下：
XGBoost-Round_1: 第一次训练样本保留量为90%
XGBoost-Round_2: 历史销量用21天销量中位数无量纲，第一次训练样本保留量为75%。

|XGBoost	|objective	|max_depth |	learning_rate	|n_estimators|	reg_alpha|	reg_lambda|
|:---:	|:---:	|:---: |:---:	|:---:|:---:|:---:|
|Round_1|	reg:linear|	3|	0.1	|500	|0	|1|
|Round_2	|reg:linear|	5|	0.03|	1600|	1|	0|
GBDT: 第一次训练样本保留量为90%。

|GBDT|	loss|	max_depth|	learning_rate|	n_estimators|	alpha|
|:---:	|:---:	|:---: |:---:	|:---:|:---:|
|Round_1|lad	|3|	0.1	|500	|0.95|
|Round_2|	lad	|5|	0.1	|500|	0.95|


### 3.2 历史均值模型

- 输入:过去21天的历史销量，过去三周的销量相关度矩阵。
- 输出：未来2周的销量及其对应在模型融合中置信度。
- 方法：过去21天的按工作日平均，得到按工作日平均的均值销量。通过过去三周按周统计的销量中位数及平均值，做线性拟合得到销量增量。将历史均值销量叠加销量增量即得到未来2周预测销量。
- 由于方法本质上寻找历史上相似的(过去三周相关度较高)销量曲线作为未来预测，本质上为均值模型与KNN方法的结合。
- 置信度即为融合系数，仅当三周相关系数或后两周相关系数的最小值大于0.7时有效。均值模型的融合比例最大为0.75。融合系数计算方法为：
<div  align="center"> <img src="http://static.zybuluo.com/Jessy923/gxdn8nohm2qsvayrgri4hbh3/eq1png.png" width="300" height="60" alt="Item-based filtering" /></div>


### 3.3 双11销量修正模型
- 特征描述：仅包含商家特征，包含平均View/Pay比值，平均每天开店时间，关店时间，开店总时长；首次营业日期，非节假日销量中位数，节假日销量中位数，节假日/非节假日销量比值；商家类别，人均消费，评分，评论数，门店等级。
- 双11销量增量，计算方法为2015-11-11当天销量V20151111与其前后两周对应工作日V20151028，V20151104，V20151118，V20151125的加权销量的比值,权重系数分别为0.15,0.35,0.35,0.15.
<div  align="center"> <img src="http://static.zybuluo.com/Jessy923/5iyvh7olsr32dncmn49vuilo/eq2.png" width="480" height="75" alt="Item-based filtering" /></div>
- 训练方法: 采用xgboost单模型训练，由于双11当天对应的工作日不同，2015年数据并不能很好反映出2016年双11节假日情况，且超市便利店类商店存在大量的数据缺失。为防止过拟合，参数设置均较为保守，最大深度为2，且加了较大的L1正则项，具体如下: max_depth = 2, learning_rate=0.01, n_estimators=500, reg_alpha=10, gamma = 1

### 3.4 模型融合
1. 多套gradient boosting的结果间的融合
xgboost1，xgboost2, GBDT三份结果按0.47, 0.34, 0.19 比例融合。
2. gradient boosting与均值模型融合
将均值模型结果与Step1产生GBDT的结果融合，均值模型的融合系数为通过相关度得到的置信度。 
3. 双11系数进行销量调制
双11当天销量乘以双11销量修正模型得到的销量增量，11-12, 11-13由于为周六周日，有理由相信其销量与11-11(周五)的表现存在相似性， 因而乘以0.2及0.1倍的销量增量系数 。


## 4 精简版的特征、模型与结果
由测评获得的Loss提升表格如下，按特征的重要性排序，分别为：历史销量特征，节假日特征，降水天气特征，商家特征。

|方案	|Loss|
|:---:	|:---:|
|最后三周按工作日平均|	0.895|
|最后六周按工作日平均，乘1.05系数|	0.860|
|Xgboost+最后三周销量特征|	0.824|
|上述增加，节假日特征|	0.813|
|上述，增加天气，商家特征	|0.798|
|上述，预训练剔除10%脏数据|	0.791|
|上述，测试集10月缺失数据填补	|0.788|
|增加双11节假日修正模型	|0.780|
|Xgboost + GBDT模型融合	|0.774|
|上述按相关系数融合平均销量|	0.772|






## 5 代码说明
**Step1**：生成精简版本user_pay, uer_view 表格

    data_new/table_regenerate.py
    
按小时统计商户销量，并进行用户异常刷单清理，生成精简版本的pay和view表格分别为，user_pay_new.csv 和 user_view_new.csv，文件大小减小为之前的1/10已便后续访问及特征提取。

**Step2**：外部数据爬取

    additional/Weather_underground_day.py
从https://www.wunderground.com 按天读取机场所在地信息，爬取信息包含7列分别为[Port, Date, Precip , Rise_act, Rise_cil, Set_act, Set_cil]，对应内容为[机场代号，日期，降水量，真实日出时间，修正日出时间，真实日落时间，修正日落时间]。


    additional/Weather_underground_hour.py

从https://www.wunderground.com 按小时读取机场所在地信息，爬取信息包含14列分别为[Port, Date, Time, Temp, Bodytemp, Dew, Humidity, Pressure, Visibility, Wind_dir, Wind_speed, Gust_speed, Event, Condition]，对应内容为[机场代号，日期，时间，气温，体感温度，露点，湿度，压力，能见度，风向，风速，阵风强度，气象事件，气象条件]。

**Step3**：特征生成

    feature/ WEATHER_FEATURES.py    

生成天气特征表 WEATHER_FEATURES.csv，包含四项，分别为人体舒适度SSH值，SSH值日增量，降水指数，天晴指数。

    feature/ SHOP_FEATURES.py
生成商家特征表SHOP_FEATURES.csv，包含平均View/Pay比值，平均每天开店时间，关店时间，开店总时长；首次营业日期，非节假日销量中位数，节假日销量中位数，节假日/非节假日销量比值；商家类别，人均消费，评分，评论数，门店等级。

    feature/ TEST_SELLS.py
生成测试集历史过去三周销量表格，修正异常销量，以历史过去14天销量的 为限制，其中 为均值， 为均方根

    feature/FEATURE_MERGE.py
整合所有特征，生成方便训练模型读取的X.csv, Y.csv, Xtest.csv三个表格

**Step4**：常规销量模型训练

    model/xgb_model1.py，model/xgb_model2.py，model/ GBDT_model.py

GBDT模型，详见3.1

    model/correlation_model.py
均值模型，详见3.2

**Step5**：双11修正系数训练

    model/ DOU11_model.py
    
双11修正模型，获得双11当天销量增加百分比

**Step6**：模型融合

    model/model_blend.py
    
各模型融合并作双11修正生成最终提交结果

## 6 总结展望
1. 赛题关键在于各个商店总体销量预测，需要对于历史整体趋势有很好把握。预测日期11月1日到11月14日区间，由于距离国庆假期较近，容易受到脏数据干扰，因而特征提取过程中仅采用过去三周的销量作为特征。现有的解决方案中，对于周期更长的趋势仍把握不足。
2. 预测日期包含了双11，给预测增加了难度。现有方案采用2015年的商家情况预测2016年，存在着诸多不足。比如两者并不在同一个工作日，2015年缺少大量超市类数据等。可能需要通过更多的相似节假日(圣诞，七夕)挖掘商家销量规律。
3. 现有方法本质上没有体现出“时间序列”这一关键因素。对于销量这一核心特征，应更多考虑在时间维度上的表现。前期曾考虑采用CNN抽取销量时间特征，后期由于精力有限放弃。


  [1]: http://static.zybuluo.com/Jessy923/k6olhzfz2si5p3n57d5w306x/costF.png
  [2]: http://static.zybuluo.com/Jessy923/bsw2bmxrm5xx4vmt3tu8pujr/pipeline.JPG
  [3]: http://static.zybuluo.com/Jessy923/gxdn8nohm2qsvayrgri4hbh3/eq1png.png
  [4]: http://static.zybuluo.com/Jessy923/5iyvh7olsr32dncmn49vuilo/eq2.png
  [5]: http://static.zybuluo.com/Jessy923/6jv0uky4zgixeb908p3exyh7/CodeCogsEqn.png
  [6]: http://static.zybuluo.com/Jessy923/9akt97ki85bpnyg2rmn3elrn/sigma.png
  [7]: http://static.zybuluo.com/Jessy923/ragtl6gap10a6esjjiil9vjq/eq1.png