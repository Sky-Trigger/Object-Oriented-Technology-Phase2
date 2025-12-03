# 程序入口，启动GUI界面
from ui.gui import launch_gui
from core.controller import GameController


def main():
    # 启动GUI
    controller = GameController()
    launch_gui(controller)


if __name__ == "__main__":
    main()
