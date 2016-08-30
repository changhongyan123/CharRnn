#charRnn
用character-level的方式建模\n
先将所有出现的符号放入数组，并将其与下标对应
再利用one-hot对每一个符号进行构建
在训练character的时候利用了三层卷积层
将输出作为输入传入双向-LSTM模型中
进行训练



first.py是参考的代码，不可以运行
tset.py可以运行
