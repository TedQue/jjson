jjson - 支持注释的 json 和 javascript 对象解析模块
by Que's C++ Studio

主要特性:
1. 支持 # 注释,从 # 开始到行尾的字符将被忽略
2. 支持 JavaScript 对象解析为 Python 字典

缺点:
1. 递归实现,解析超大字符串时可能导致栈溢出
2. 性能较差,适用于解析较短字符串以及对性能不敏感的场景


querw
2021/9/23
