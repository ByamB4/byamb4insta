# MrInsta
Automate the process of obtaining free Instagram followers using Mr. Insta
- Full vlog [youtube](https://youtu.be/WQyZ7So0mrA) 

- The `MrInsta.login` function may occasionally fail even with correct credentials due to server issues, especially if there are too many accounts. 

- Create fake users in [https://app.mrinsta.com](https://app.mrinsta.com/) then copy to `users.json`
- Update your `.env` file
- Update your `main.py/TARGET`
- How to use [youtube](https://youtu.be/_9Hc-cdZ_c8) 

- `CreateAccounts`

  - The process of bypassing OTP and creating accounts can be automated, but we are currently unable to automate Instagram verification. However, we have a solution suggested by @Emotulgaa, which involves using a list of existing accounts in the followers.txt file. This method can be time-consuming, as some of the accounts in the list may already be taken by @Emotulgaa or @ByamB4.

### Need help

- Automating Instagram account verification

  - While we can use the `followers.txt` file as a workaround, it is not an optimal solution. We need a runtime solution that can fetch public Instagram usernames.

- `MrInsta.redeem_earned_coin`

  - The current logic of this function is not optimized and needs improvement to make the code more readable and efficient.

- GUI application

  - In order to make this code more user-friendly for a wider audience, we need to develop a graphical user interface (GUI) and export it as an .exe file. While Electron is a cool option, the final size of the application is very large. We are currently considering creating a Python GUI application using tkinter, but are still exploring different options.
