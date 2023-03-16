import pandas

x = pandas.Series([False, False, True, False, False])
y = x.iloc[1:len(x)].append(pandas.Series([False]))
y.index = range(len(y))

print(x)
print(y)
