---
name: qmt-strategy
description: "迅投QMT量化交易策略开发。包括QMT内置Python API详解、策略模板（双均线、网格、MACD、回踩反弹）、实盘/回测下单函数、行情数据获取、账户持仓查询。当用户要求编写QMT策略、了解QMT API、或在QMT平台实现交易逻辑时触发。"
agent_created: true
---

# QMT (迅投极速策略交易系统) 量化交易策略开发

## 重要说明

- 所有策略文件必须以 `#coding:gbk` 开头（QMT内置编辑器的编码要求）。
- 策略包含两个核心函数：`init(ContextInfo)` 和 `handlebar(ContextInfo)`。
- 核心对象 `ContextInfo` 是API的"灵魂"，封装了所有属性和方法。

---

## 一、策略基础框架

### 1.1 核心函数

```python
#coding:gbk

def init(ContextInfo):
    """初始化函数，策略启动时执行一次"""
    # 设置账号
    ContextInfo.set_account(account)
    # 设置股票池
    ContextInfo.set_universe(['000001.SZ', '000002.SZ'])
    # 订阅行情
    ContextInfo.subscribe_quote(['000001.SZ', '000002.SZ'])
    # 设置回测参数（回测时用）
    # ContextInfo.start = '20240101'
    # ContextInfo.end = '20240618'
    # ContextInfo.capital = 100000  # 初始资金
    # 设置手续费/滑点
    # ContextInfo.set_commission(0, [佣金万2.5, 印花税千1, 过户费万0.1])
    # ContextInfo.set_slippage(0, 0.01)  # 滑点0.01元
    # 启动定时器
    ContextInfo.run_time('my_timer', '1m', '2024-01-01', market='SH')

def handlebar(ContextInfo):
    """每根K线收盘/每个tick到来时执行"""
    # 获取当前时间
    bar_time = ContextInfo.get_bar_time_tag()
    # 核心交易逻辑写在这里
    pass

def stop(ContextInfo):
    """策略停止时清理（非必须）"""
    pass
```

### 1.2 ContextInfo 常用属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `ContextInfo.accID` | str | 当前账号ID |
| `ContextInfo.do_backtest` | bool | 是否回测模式 |
| `ContextInfo.start` | str | 回测开始日期 |
| `ContextInfo.end` | str | 回测结束日期 |
| `ContextInfo.capital` | int | 回测初始资金 |
| `ContextInfo.benchmark` | str | 回测基准品种 |
| `ContextInfo.universe` | list | 当前关注的股票列表 |

---

## 二、行情数据获取

### 2.1 获取K线数据 (核心)

```python
# get_market_data_ex(fields, stockCodes, period, count, ...)
# fields: 要获取的字段列表，None表示获取所有字段
# stockCodes: 股票代码列表
# period: K线周期 ('1m', '5m', '15m', '30m', '1d' 等)
# count: 获取的K线数量

# 获取最近30根日K线
df = ContextInfo.get_market_data_ex(
    fields=['close', 'open', 'high', 'low', 'volume', 'amount'],
    stockCodes=['000001.SZ'],
    period='1d',
    count=30
)

# df 是一个 dict，key是股票代码，value是DataFrame
# df['000001.SZ']['close'] 获取收盘价序列
```

### 2.2 获取Tick数据

```python
# 获取最新分笔数据
tick = ContextInfo.get_full_tick(['000001.SZ'])
# tick结构: {'000001.SZ': {'lastPrice': 最新价, 'bid': 买价, 'ask': 卖价, ...}}
```

### 2.3 获取历史数据（简化版）

```python
# 获取最近30根日K线（简化接口）
hist = ContextInfo.get_history_data(period='1d', count=30, stockCodes='000001.SZ')
```

### 2.4 获取品种信息

```python
# 获取合约详细信息
detail = ContextInfo.get_instrument_detail('000001.SZ')
# 返回dict: {'InstrumentID': 代码, 'InstrumentName': 名称, ...}

# 获取板块成份股
stocks = ContextInfo.get_stock_list_in_sector('上证50')
stocks = ContextInfo.get_sector('000016.SH')  # 上证50指数
stocks = ContextInfo.get_industry('SW', '银行')  # 申万银行行业
```

### 2.5 获取财务数据

```python
# 获取财务数据
fin_data = ContextInfo.get_financial_data(
    stockCodes=['000001.SZ'],
    fields=['PELYR', 'PB'],  # 市盈率、市净率等
    date='20240101'
)
```

---

## 三、交易下单函数

### 3.1 passorder - 综合下单函数 (实盘推荐)

```python
passorder(opType, orderType, accountid, orderCode, prType, price, volume, 
          strategyName, quickTrade, userOrderId, ContextInfo)
```

**参数详解：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `opType` | int | 交易类型：23=买入, 24=卖出；期货: 0=买入开仓, 1=卖出开仓, 3=卖出平仓, 4=买入平仓 |
| `orderType` | int | 下单方式：1101=按股数/手数, 1102=按金额(元), 1103=按百分比(%) |
| `accountid` | str | 资金账号。策略中可直接用 `account` 变量 |
| `orderCode` | str | 股票代码，格式 '000001.SZ' / 'rb2405.SF' |
| `prType` | int | 报价类型：5=最新价, 11=指定价, 12=市价, 14=对手价, 买1到买5=1-5, 卖1到卖5=6-10 |
| `price` | float | 指定价有效。其他prType填-1或0占位 |
| `volume` | int | 交易量。正数买入，负数卖出。单位由orderType决定 |
| `strategyName` | str | 策略名称（可选） |
| `quickTrade` | int | 0=等待下一K线触发, 1=非历史bar立即触发, 2=立即触发(回测也能触发) |
| `userOrderId` | str | 自定义委托号（可选） |
| `ContextInfo` | class | 固定参数 |

**使用示例：**

```python
# 股票：最新价买入100股平安银行
passorder(23, 1101, account, '000001.SZ', 5, -1, 100, '策略1', 1, '', ContextInfo)

# 股票：指定价卖出
passorder(24, 1101, account, '000001.SZ', 11, 15.50, -100, '', 1, '', ContextInfo)

# 期货：对手价买入开仓2手螺纹钢
passorder(0, 1101, account, 'rb2410.SF', 14, -1, 2, '', 1, '', ContextInfo)

# 按金额买入（全部买入）
passorder(23, 1202, account, '000001.SZ', 5, -1, 50000, '全仓买入', 1, '', ContextInfo)
```

### 3.2 algo_passorder - 算法下单（拆单）

```python
algo_passorder(opType, orderType, accountid, orderCode, prType, price, volume, 
               strategyName, quickTrade, userOrderId, userOrderParam, ContextInfo)

userparam = {
    "OrderType": 1,          # 0=普通, 1=算法交易, 2=随机量
    "MaxOrderCount": 20,     # 最多拆成20笔
    "SuperPriceType": 1,     # 0=按比例, 1=按数值
    "SuperPriceValue": 1.12, # 超价1.12元
}
algo_passorder(23, 1101, accid, '000001.SZ', 5, 15, 1000, '', 1, '', userparam, ContextInfo)
```

### 3.3 撤单/任务管理

```python
# 撤单
cancel(orderId, accountId, 'STOCK', ContextInfo)  # 返回bool
cancel(orderId, accountId, 'FUTURE', ContextInfo)

# 撤销算法任务
cancel_task(taskId, accountId, 'STOCK', ContextInfo)

# 暂停/继续算法任务
pause_task(taskId, accountId, 'STOCK', ContextInfo)
resume_task(taskId, accountId, 'STOCK', ContextInfo)
```

### 3.4 回测专用下单函数（仅在回测中生效）

```python
# 按股数下单
order_shares('000001.SZ', 100, ContextInfo, account)

# 按手数下单
order_lots('000001.SZ', 1, ContextInfo, account)

# 按价值下单（元）
order_value('000001.SZ', 50000, ContextInfo, account)

# 按比例下单（占总资产%）
order_percent('000001.SZ', 0.5, ContextInfo, account)  # 50%仓位

# 调仓至目标
order_target_value('000001.SZ', 100000, ContextInfo, account)  # 调整至10万市值
order_target_percent('000001.SZ', 0.3, ContextInfo, account)   # 调整至30%仓位
```

---

## 四、账户与持仓查询

### 4.1 get_trade_detail_data - 核心查询函数

```python
get_trade_detail_data(accountID, strAccountType, strDatatype, strategyName)
```

- `strAccountType`: 'STOCK'(股票), 'FUTURE'(期货), 'CREDIT'(两融)
- `strDatatype`: 'ACCOUNT'(账户), 'POSITION'(持仓), 'ORDER'(委托), 'DEAL'(成交), 'TASK'(任务)

```python
# 查询账户资金
accounts = get_trade_detail_data(account, 'STOCK', 'ACCOUNT')
for acc in accounts:
    balance = acc.m_dBalance      # 总资产
    available = acc.m_dAvailable  # 可用资金
    frozen = acc.m_dFrozen        # 冻结资金
    market_value = acc.m_dMarketValue  # 持仓市值

# 查询持仓
positions = get_trade_detail_data(account, 'STOCK', 'POSITION')
for pos in positions:
    code = pos.m_strInstrumentID   # 证券代码
    volume = pos.m_nVolume         # 持仓数量
    avl_volume = pos.m_nCanUse     # 可用数量
    cost = pos.m_dOpenPrice        # 成本价
    price = pos.m_dPrice           # 现价
    profit = pos.m_dProfit         # 浮动盈亏
    profit_ratio = pos.m_dProfitRate  # 盈亏比例

# 查询当日委托
orders = get_trade_detail_data(account, 'STOCK', 'ORDER')
for order in orders:
    code = order.m_strInstrumentID
    volume = order.m_nVolume        # 委托数量
    price = order.m_dPrice          # 委托价格
    status = order.m_nOrderStatus   # 状态
    deal_vol = order.m_nDealVolume  # 成交数量

# 查询当日成交
deals = get_trade_detail_data(account, 'STOCK', 'DEAL')
for deal in deals:
    code = deal.m_strInstrumentID
    price = deal.m_dPrice           # 成交价
    volume = deal.m_nVolume         # 成交数量
    amount = deal.m_dAmount         # 成交金额
```

### 4.2 持仓判断辅助

```python
def get_position(code, ContextInfo):
    """查询某只股票的持仓数量"""
    positions = get_trade_detail_data(ContextInfo.accID, 'STOCK', 'POSITION')
    for pos in positions:
        if pos.m_strInstrumentID == code:
            return pos.m_nVolume  # 持仓数量
    return 0

def get_available_cash(ContextInfo):
    """获取可用资金"""
    accounts = get_trade_detail_data(ContextInfo.accID, 'STOCK', 'ACCOUNT')
    return accounts[0].m_dAvailable if accounts else 0
```

---

## 五、常用策略模板

### 5.1 双均线策略

```python
#coding:gbk

def init(ContextInfo):
    ContextInfo.set_account(account)
    ContextInfo.set_universe(['000001.SZ'])
    ContextInfo.subscribe_quote(['000001.SZ'])

def handlebar(ContextInfo):
    code = '000001.SZ'
    
    # 获取日K线数据
    df = ContextInfo.get_market_data_ex(
        fields=['close'], stockCodes=[code], period='1d', count=60
    )
    close = df[code]['close'].values
    
    if len(close) < 60:
        return
    
    # 计算均线
    ma5 = sum(close[-5:]) / 5
    ma20 = sum(close[-20:]) / 20
    ma5_prev = sum(close[-6:-1]) / 5
    ma20_prev = sum(close[-21:-1]) / 20
    
    # 查询持仓
    pos = 0
    positions = get_trade_detail_data(ContextInfo.accID, 'STOCK', 'POSITION')
    for p in positions:
        if p.m_strInstrumentID == code:
            pos = p.m_nVolume
            break
    
    # 金叉买入
    if ma5 > ma20 and ma5_prev <= ma20_prev and pos == 0:
        passorder(23, 1101, account, code, 5, -1, 100, '金叉买入', 1, '', ContextInfo)
    
    # 死叉卖出
    if ma5 < ma20 and ma5_prev >= ma20_prev and pos > 0:
        passorder(24, 1101, account, code, 5, -1, -pos, '死叉卖出', 1, '', ContextInfo)
```

### 5.2 网格交易策略

```python
#coding:gbk

def init(ContextInfo):
    ContextInfo.set_account(account)
    ContextInfo.set_universe(['000001.SZ'])
    ContextInfo.subscribe_quote(['000001.SZ'])
    
    # 网格参数
    global grid_params
    grid_params = {
        'code': '000001.SZ',
        'base_price': 10.0,    # 基准价
        'grid_size': 0.2,      # 网格间距
        'qty_per_grid': 100,   # 每格数量
        'max_pos': 500,        # 最大持仓
        'min_hold': 300        # 底仓 空头网格（先买后卖）
    }

def handlebar(ContextInfo):
    tick = ContextInfo.get_full_tick([grid_params['code']])
    if grid_params['code'] not in tick:
        return
    
    price = tick[grid_params['code']]['lastPrice']
    base = grid_params['base_price']
    step = int((price - base) / grid_params['grid_size'])
    
    # 查持仓
    pos = 0
    positions = get_trade_detail_data(ContextInfo.accID, 'STOCK', 'POSITION')
    for p in positions:
        if p.m_strInstrumentID == grid_params['code']:
            pos = p.m_nVolume
            break
    
    cash = 0
    accounts = get_trade_detail_data(ContextInfo.accID, 'STOCK', 'ACCOUNT')
    if accounts:
        cash = accounts[0].m_dAvailable
    
    need_pos = grid_params['min_hold'] - step * grid_params['qty_per_grid']
    need_pos = max(0, min(grid_params['max_pos'], need_pos))
    
    if need_pos > pos and cash > price * grid_params['qty_per_grid'] * 1.5:
        buy_qty = need_pos - pos
        passorder(23, 1101, account, grid_params['code'], 5, -1, 
                  buy_qty, '网格买入', 1, '', ContextInfo)
    elif need_pos < pos:
        sell_qty = pos - need_pos
        passorder(24, 1101, account, grid_params['code'], 5, -1, 
                  -sell_qty, '网格卖出', 1, '', ContextInfo)
```

### 5.3 MACD顶底背离策略

```python
#coding:gbk

def init(ContextInfo):
    ContextInfo.set_account(account)
    ContextInfo.set_universe(['000001.SZ'])
    ContextInfo.subscribe_quote(['000001.SZ'])

def ema(data, n):
    """计算EMA"""
    result = [data[0]]
    alpha = 2 / (n + 1)
    for i in range(1, len(data)):
        result.append(alpha * data[i] + (1 - alpha) * result[-1])
    return result

def macd(close, fast=12, slow=26, signal=9):
    """计算MACD"""
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    dif = [ema_fast[i] - ema_slow[i] for i in range(len(close))]
    dea = ema(dif, signal)
    bar = [2 * (dif[i] - dea[i]) for i in range(len(close))]
    return dif, dea, bar

def handlebar(ContextInfo):
    code = '000001.SZ'
    df = ContextInfo.get_market_data_ex(
        fields=['close'], stockCodes=[code], period='1d', count=60
    )
    close = df[code]['close'].values
    
    if len(close) < 60:
        return
    
    dif, dea, bar = macd(close.tolist())
    
    # 金叉买入
    if bar[-1] > 0 and bar[-2] <= 0:
        pos = 0
        for p in get_trade_detail_data(ContextInfo.accID, 'STOCK', 'POSITION'):
            if p.m_strInstrumentID == code:
                pos = p.m_nVolume
        if pos == 0:
            passorder(23, 1101, account, code, 5, -1, 100, 'MACD金叉', 1, '', ContextInfo)
    
    # 死叉卖出
    if bar[-1] < 0 and bar[-2] >= 0:
        pos = 0
        for p in get_trade_detail_data(ContextInfo.accID, 'STOCK', 'POSITION'):
            if p.m_strInstrumentID == code:
                pos = p.m_nVolume
        if pos > 0:
            passorder(24, 1101, account, code, 5, -1, -pos, 'MACD死叉', 1, '', ContextInfo)
```

### 5.4 回踩反弹策略（匹配用户选股风格）

```python
#coding:gbk

def init(ContextInfo):
    ContextInfo.set_account(account)
    # 关注标的
    stocks = ['603308.SH', '300738.SZ', '603678.SH', '000970.SZ', 
              '603267.SH', '600367.SH', '600552.SH', '603629.SH', '603773.SH']
    ContextInfo.set_universe(stocks)
    ContextInfo.subscribe_quote(stocks)

def handlebar(ContextInfo):
    for code in ContextInfo.universe:
        df = ContextInfo.get_market_data_ex(
            fields=['close', 'high', 'low', 'volume', 'amount'],
            stockCodes=[code], period='1d', count=60
        )
        close_series = df[code]['close'].values
        high_series = df[code]['high'].values
        low_series = df[code]['low'].values
        vol_series = df[code]['volume'].values
        
        if len(close_series) < 30:
            continue
        
        # 60日涨幅为正
        gain_60d = (close_series[-1] / close_series[-20] - 1) * 100  # 用最近20根近似
        if gain_60d <= 0:
            continue
        
        # 距52周高还有空间
        high_52w = max(high_series[-20:])  # 近似
        space_pct = (1 - close_series[-1] / high_52w) * 100
        if space_pct < 5:
            continue
        
        # 量比＞0.6（近5日均量/近20日均量）
        vol_5 = sum(vol_series[-5:]) / 5
        vol_20 = sum(vol_series[-20:]) / 20
        vol_ratio = vol_5 / vol_20 if vol_20 > 0 else 0
        
        if vol_ratio < 0.6:
            continue
        
        # MACD金叉信号
        # 简化的MACD金叉判断
        ema12_prev = sum(close_series[-13:-1]) / 12  # 近似
        ema26_prev = sum(close_series[-27:-1]) / 26  # 近似
        ema12 = sum(close_series[-12:]) / 12
        ema26 = sum(close_series[-26:]) / 26
        
        dif_prev = ema12_prev - ema26_prev
        dif = ema12 - ema26
        
        # 回踩反弹：DIF转正
        if dif > 0 and dif_prev <= 0:
            # 检查持仓
            pos = 0
            for p in get_trade_detail_data(ContextInfo.accID, 'STOCK', 'POSITION'):
                if p.m_strInstrumentID == code:
                    pos = p.m_nVolume
            
            if pos == 0:
                # 开盘买入
                passorder(23, 1101, account, code, 5, -1, 
                          100, '回踩反弹', 1, '', ContextInfo)
```

---

## 六、回调函数

```python
# 委托状态变化回调
def order_callback(ContextInfo):
    pass

# 成交回调
def deal_callback(ContextInfo):
    pass

# 持仓变化回调
def position_callback(ContextInfo):
    pass

# 资金变化回调
def account_callback(ContextInfo):
    pass

# 异常下单回调
def orderError_callback(ContextInfo):
    pass
```

---

## 七、定时器与辅助函数

```python
# 设置定时器
ContextInfo.run_time('my_func', '1m', '2024-01-01', market='SH')
# 参数：函数名、周期、开始时间、市场

# 判定是否为最后一根K线
ContextInfo.is_last_bar()

# 判定是否为新的K线
ContextInfo.is_new_bar()

# 获取当前K线时间戳（毫秒）
ContextInfo.get_bar_time_tag()

# 时间戳转日期
timetag_to_datetime(timetag, format='%Y-%m-%d %H:%M:%S')

# 画图（在K线界面上）
ContextInfo.paint('MA5', ma5_values, 'red', 1)
ContextInfo.draw_text(x, y, '买入信号', 'red')
ContextInfo.draw_icon(x, y, 1, 'red')  # 1=买入图标, -1=卖出图标
```

---

## 八、策略编写注意事项

1. **实盘用passorder，回测用order_shares等**：passorder在实盘和模拟盘有效，order_shares等在回测中有效。
2. **非历史bar下单**：`quickTrade=1` 确保信号触发后立即下单，不等到下一根K线。
3. **编码必须gbk**：QMT内置编辑器不支持UTF-8。
4. **区分STOCK和FUTURE**：查询和下单时的账号类型要匹配。
5. **回测参数设置**：在init中设置 `ContextInfo.start/end/capital`。
6. **策略名标记**：在passorder中设置strategyName，方便后续查询筛选。
7. **持仓查询**：始终通过get_trade_detail_data查询实时持仓，不要依赖本地变量。
8. **手数 vs 股数**：orderType=1101时，股票按股、期货按手。
