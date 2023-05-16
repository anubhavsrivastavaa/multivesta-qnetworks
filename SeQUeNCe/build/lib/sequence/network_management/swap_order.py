import copy
name = 2
path = [1,2,3,4,5,6,7,8]
swap_order = {}
for p in path[1:-1]:
    _path = copy.deepcopy(path)
    while _path.index(p) % 2 == 0:
        new_path = []
        for i, n in enumerate(_path):
            if i % 2 == 0 or i == len(_path) - 1:
                new_path.append(n)
        _path = new_path
    print(f'{p} : {_path}')
    swap_order[p] = len(_path)
    print(swap_order)

nd = [k for k, v in sorted(swap_order.items(), key=lambda item: item[1], reverse=True)]
print(nd)