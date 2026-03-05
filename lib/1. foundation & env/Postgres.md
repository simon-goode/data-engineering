
```postgresql
extract(field from source)
```
Works with `year`, `month`, `day`, `hour`, `week`, `epoch`, `century`, `decade`, `dow`, `quarter`, etc.

```postgresql
rollup(cols)
```
Group by that also provides subtotals by subdivision of columns and grand total

```postgresql
to_char(field, format)
```
Converts data to the format specified (`999.99` for 2 decimal places, `YYYY-MM-DD`, etc.)

