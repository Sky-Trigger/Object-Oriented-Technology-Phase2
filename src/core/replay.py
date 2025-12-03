# 录像回放模块，处理录像的播放和控制
from core.models import Move, move_from_payload


class ReplayManager:
    def __init__(self, moves, game_type, board_size):
        self.moves = moves
        self.game_type = game_type
        self.board_size = board_size
        self.current_index = -1
        self.is_playing = False

    def start_replay(self):
        # 开始回放
        self.current_index = -1
        self.is_playing = True

    def next_move(self):
        # 获取下一个移动
        if self.current_index + 1 < len(self.moves):
            self.current_index += 1
            return self.moves[self.current_index]
        return None

    def previous_move(self):
        # 获取上一个移动
        if self.current_index > 0:
            self.current_index -= 1
            return self.moves[self.current_index]
        return None

    def jump_to(self, index):
        # 跳转到指定步数
        if 0 <= index < len(self.moves):
            self.current_index = index
        elif index < 0:
            self.current_index = -1
        else:
            self.current_index = len(self.moves) - 1

    def stop_replay(self):
        # 停止回放
        self.is_playing = False

    def get_current_board_state(self):
        # 获取当前回放的棋盘状态（需要结合引擎）
        # 这里返回移动列表的前current_index+1步
        return self.moves[: self.current_index + 1]

    def is_finished(self):
        # 检查回放是否结束
        return self.current_index >= len(self.moves) - 1
