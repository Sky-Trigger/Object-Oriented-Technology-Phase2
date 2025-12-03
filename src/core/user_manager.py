# 用户账户管理模块，处理注册、登录和战绩记录
import json
import os
from core.models import PlayerColor


class UserManager:
    def __init__(self, data_file="users.json"):
        self.data_file = data_file
        self.users = self._load_users()
        self.current_user = None

    def _load_users(self):
        # 加载用户数据
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_users(self):
        # 保存用户数据
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)

    def register(self, username, password):
        # 用户注册
        if username in self.users:
            raise ValueError("用户名已存在")
        self.users[username] = {"password": password, "games_played": 0, "wins": 0}
        self._save_users()

    def login(self, username, password):
        # 用户登录
        if username not in self.users:
            raise ValueError("用户名不存在")
        if self.users[username]["password"] != password:
            raise ValueError("密码错误")
        self.current_user = username
        return True

    def login_guest(self):
        # 游客登录
        self.current_user = "游客"

    def logout(self):
        # 用户登出
        self.current_user = None

    def get_current_user(self):
        # 获取当前用户
        return self.current_user

    def update_stats(self, winner_color, player_color=None):
        # 更新战绩：当当前登录用户与玩家颜色匹配时更新胜场
        if not self.current_user or self.current_user == "游客":
            return
        user = self.users[self.current_user]
        user["games_played"] += 1
        if player_color is not None and winner_color == player_color:
            user["wins"] += 1
        self._save_users()

    def get_stats(self, username=None):
        # 获取战绩
        user = username or self.current_user
        if not user or user not in self.users:
            return {"games_played": 0, "wins": 0}
        return self.users[user]
