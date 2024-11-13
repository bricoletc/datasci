# datasci

## Tents: tabular entries

```python
from datasci import Tents

header = ["col1", "col2", "col3"]
tents = Tents(header=header)
for val1, val2, val3 in zip([1,2], [3,4], [5,6]):
    new_tent = tents.new()
    new_tent.update(col1=val1)
    new_tent.col2 = val2
    new_tent["col3"] = val3
    tents.add(new_tent)
with open("outfile.tsv", "w") as ofstream:
    print(tents, file=ofstream)
```

```sh
$cat outfile.tsv
col1	col2	col3
1	3	5
2	4	6
```
