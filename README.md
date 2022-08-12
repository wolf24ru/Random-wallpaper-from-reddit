# Random-wallpaper
(ru) Загрузка и установка случайных обоев и [ze-robot](https://www.reddit.com/user/ze-robot/?sort=new) и [r-wallpaper](https://www.reddit.com/r/wallpaper/new/).

(en)Download and install random wallpaper from [ze-robot](https://www.reddit.com/user/ze-robot/?sort=new) and [r-wallpaper](https://www.reddit.com/r/wallpaper/new/). 

> **_NOTE:_** At the moment, the code is relevant only for Linux **Mint**.
___

### To run the code:
- Go to the folder with `Wall.py `;
- Call the terminal;
- Install >=[python 3.10](https://www.python.org/downloads/)
- Create `secret.py` file 
- In secret.py write data from [your app in reddit](https://www.reddit.com/prefs/apps)
- Run the following command:
```shell
python3 Wall.py 
```
___
In secret.py must be:
```shell
client_id = 'client_id'
client_secret = 'client_secret'
user_agent = 'Wallpaper_or_other_app_name' 
```

___
At now in app you can download images from 2 resource:
 - [ze-robot](https://www.reddit.com/user/ze-robot/)
 - [r-wallpaper](https://www.reddit.com/r/wallpaper/)

In default resource is `ze-robot`, but you can change that. For this you need to run program with the prefix `-r` chuse resource:

```bash
python Wall.py -r r-wallpaper
```
___

App in  default choosing  random image from the 20 images. You can chose limit quantity images for selection using prefix `-l`:
```bash
python Wall.py -l 50
```
___

For change path to save current image use prefix `-f`:
```bash
python Wall.py -f ~/path/to/file
```



