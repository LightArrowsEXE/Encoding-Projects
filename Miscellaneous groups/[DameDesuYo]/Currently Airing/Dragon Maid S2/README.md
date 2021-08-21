Note: Some episodes are "missing" because I occasionally let others handle it on their side if I'm unavailable.
The scripts remain largely the same, but the dehardsubbing ranges will be different, so there's not much lost.

# Setup

My encoding environment for this project.
This setup requires a couple of dependencies.
You can install the easy-to-get ones with the following command:

```bash
$ pip3 install -r requirements.txt
```

Since this is a non-exhaustive list,
you may have to find the other dependencies by googling them.
Please be aware that a couple dependencies are very prone to change,
so you may be forced to rewrite parts of the script,
to uninstall the latest versions and install the correct version,
or to run these in a virtual environment.
Whichever is most convenient for you.

## Running an encode

Set the paths of `JP_src` (or other similar names) in every script to match your episodes.
Also make sure to adjust stuff like your tags and the name added to the MediaInfo to yours.
Then run the script as follows:

```bash
$ python3 script.py
```

This should handle everything,
from video/audio encoding to muxing.
You can also run this script with `vspipe` if you so choose.

```bash
$ vspipe script.py --y4m - | settings
```

But I do not guarantee that this will work properly.
