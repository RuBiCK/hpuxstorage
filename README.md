# hpuxstorage
Show the size of each vg and the amount of disk model used (EVA, XP, Virtual...)

How to use: pending write

This script produces the following output:
```
+----------+---------------+-----------+-----------+---------------------+
| Server   | VG name       |   Size Gb |   Free Gb | Disks count types   |
|----------+---------------+-----------+-----------+---------------------|
| host1    | /dev/vgoracle |         9 |         0 | 1 x  OPEN-V         |
| host1    | /dev/vg03     |         8 |         0 | 2 x  OPEN-V         |
| host1    | /dev/vg02     |       119 |         0 | 5 x  OPEN-V         |
| host1    | /dev/vg01     |         9 |         1 | 1 x  HSV400         |
| host1    | /dev/vg00     |       119 |        10 | 1 x  HSV400         |
| host1    | /dev/vg06     |      3278 |         0 | 33 x  OPEN-V        |
| host1    | /dev/vg05     |        39 |        12 | 4 x  OPEN-V         |
| host1    | /dev/vg04     |         8 |         0 | 2 x  OPEN-V         |
+----------+---------------+-----------+-----------+---------------------+


+----------+-------------+-----------+-----------+---------------------+
| Server   | VG name     |   Size Gb |   Free Gb | Disks count types   |
|----------+-------------+-----------+-----------+---------------------|
| host2    | /dev/vg03   |       999 |       237 | 2 x  Virtual Disk   |
| host2    | /dev/vg01   |         9 |         0 | 1 x  Virtual LvDisk |
| host2    | /dev/vg00   |        54 |         9 | 1 x  Virtual LvDisk |
| host2    | /dev/vgREPO |       199 |         0 | 4 x  Virtual Disk   |
+----------+-------------+-----------+-----------+---------------------+


+----------+-----------+-----------+-----------+---------------------+
| Server   | VG name   |   Size Gb |   Free Gb | Disks count types   |
|----------+-----------+-----------+-----------+---------------------|
| host3    | /dev/vg03 |       574 |        78 | 2 x  Virtual Disk   |
| host3    | /dev/vg02 |        99 |         0 | 2 x  Virtual Disk   |
| host3    | /dev/vg01 |         9 |         0 | 1 x  Virtual Disk   |
| host3    | /dev/vg00 |        61 |         0 | 1 x  Virtual Disk   |
+----------+-----------+-----------+-----------+---------------------+
```
