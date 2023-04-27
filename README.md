# MrInsta
Automate the process of obtaining free Instagram followers using Mr. Insta

### Before running the script
Make sure to follow these steps before running the script:

- Create fake users in [https://app.mrinsta.com](https://app.mrinsta.com/) then copy to `users.json`
- Update your `.env` file
- Update your `main.py/TARGET`

### Running the script
To run the script, use the following command in the terminal:

```
python main.py
```

### Cronjob
If you want to run the script automatically, you can set up a cronjob. For example, the following cronjob will run the script every hour:

```
crontab -e
0 * * * * cd <THIS_REPO_PATH>; python main.py >/tmp/mrinsta.suc 2>/tmp/mrinsta.err;
```
