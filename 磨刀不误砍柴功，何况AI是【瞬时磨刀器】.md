# 磨刀不误砍柴功，何况AI是【瞬时磨刀器】

## 背景

统计工作是枯燥的、重复的、个性的。

每个单位、每个部门、每个岗位的工作都不一样，但是一个正常的公司都需要统计工作以衡量工作量、生产量、销售量，来反应生产力。

而我作为公司统计工作的一个基石，一个标准的牛马，一直在努力研究怎么提高自己的生产效率。

## 工具演进

### 1.0 版本：手动Python脚本

刚开始都是变成来提升操作Excel的效率，就像这样：

```python
import pandas as pd
import re

# 设置格式对齐
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

# 车牌号正则表达式
re_str = '([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领]{1}[A-Z]{1}(([A-Z0-9]{5}[DF]{1})|([DF]{1}[A-Z0-9]{5})))|([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领]{1}[A-Z]{1}[A-Z0-9]{4}[A-Z0-9挂学警港澳]{1})'

df = pd.read_excel('./1.xlsx')

def confirm_transportation(x):
    x_upper = x.upper().replace('卾', '鄂')
    matches = re.findall(re_str, x_upper)
    if matches:
        return '汽提'
    else:
        user_input = input(f"确认 '{x}' 是否为装车？(y/n): ")
        return '汽提' if user_input.lower() == 'y' else '装船'

# 根据提货车号内容判断正则判断是否车牌号，否则就是装船
df['运输方式'] = df.提货车号.apply(confirm_transportation)

# 根据产地判断是否集港的方式
def categorize(x):
    if x in ['九江萍钢', '长钢', '广钢', '宁夏建龙(特钢)', '迁安九江', '萍安钢铁']:
        return '水运'
    elif x == '山西晋南':
        return '铁运'
    else:
        return '汽运'

df['类别'] = df.产地.apply(categorize)

# 分类统计
df2 = pd.pivot_table(df, index=['类别', '产地'], columns=['运输方式'], values=[
                     '实发量', '实发件数'], aggfunc=['sum'], margins=True, margins_name='合计')

# 输出
print(df2)

with pd.ExcelWriter('1.xlsx', mode='a', engine='openpyxl') as writer:
    df2.to_excel(writer, sheet_name='汇总表', index=True)
```

这是其中一个对数据表格自动分类，用来分辨水运、铁运、公路的运输方式来适配不同的价格结算方式的生成量统计工作。

但是越来越多的统计工作，我每次都需要打开vscode来找对应的工具，还需要把原始数据都重新按照python脚本命名，这样的速度已经不满足我了。

### 2.0 版本：AI助力工具箱

既然现在AI这么成熟，我何不提个要求做一个工具箱，保留扩展功能，随时根据我工作的需要来拓展这个工具箱呢。

> **需求**：使用pyqt编写一个工作工具，我每次回往里面添加功能，帮我先搞一个开发文档出来，需要留好接口，界面分明，左边最好是各个功能入口，右边是功能区，提前安排三个功能占位。我随后慢慢添加功能。

然后我与AI一拍即合，得到这样的工具：

![工具箱主界面](https://img.10an.fun/2025/12/cb22e1c9813aad9b688670c7d5d771f9.webp)

> **意外惊喜**：我本以为是占位符，但是实际上AI提供的三个插件居然都能正常使用，太惊喜了。

### 3.0 版本：月汇总工具集成

于是我把上面python的脚本给AI，让他集成到工具箱中：

> **需求**：这个程序是我的月汇总程序，把这个集成到刚才的工具中，你帮忙优化一下。

然后我就得到这个插件：

![月汇总工具界面](https://img.10an.fun/2025/12/b2f612b7e4e501f00a05cc9b6457ee42.webp)

> **功能远超预期**：它远比我想的周到，高级设置里面直接把我以前需要硬编码的内容，直接可以在这里设置，随时根据需要调整。

## 功能亮点

### 可配置的车牌号修正

![车牌号修正设置](https://img.10an.fun/2025/12/a249e74294531631b478742321623505.webp)

### 灵活的文件操作

我打开文件也只需要浏览，保存文件随时另起名，也不用怕文件被占用。并且汇总数据里面可以先预览数据再决定是否需要保存。

![文件操作界面](https://img.10an.fun/2025/12/2a5d8f83867855ce838ed8d272a8a408.webp)

### 完整的结果输出

最后保存的结果跟我之前那个脚本保存的一致，但是功能强大太多。

![结果输出界面](https://img.10an.fun/2025/12/2c3ded42a5ceba4f5dfa9805baac3ce9.webp)

## 总结

磨刀不误砍柴功，何况AI是瞬时磨刀器。原本一个简单的Python脚本，在AI的助力下，演变成了一个功能强大、可扩展的桌面应用程序，大大提高了工作效率。

有了插件工具箱以后，以后随时可以按照自己的需要添加插件功能。